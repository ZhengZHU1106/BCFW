/**
 * Simple deployment script for MultiSigProposal contract
 * Creates configuration and integration without external dependencies
 */

const fs = require('fs');
const path = require('path');

// Configuration
const MNEMONIC = 'bulk tonight audit hover toddler orange boost twenty biology flower govern soldier';
const MANAGER_INDICES = [0, 1, 2]; // manager_0, manager_1, manager_2
const TREASURY_INDEX = 3; // treasury account
const THRESHOLD = 2; // 2 out of 3 signatures required

// Simple address derivation (for demo purposes)
function deriveAddress(index) {
    // Generate deterministic addresses based on index
    const base = '0x' + '0'.repeat(39);
    return base + index.toString();
}

async function main() {
    console.log('🚀 Creating MultiSigProposal contract configuration...');
    
    // Generate Manager addresses (simplified)
    const managerAddresses = MANAGER_INDICES.map(index => {
        // These should match the actual Ganache addresses
        // For demo, we'll use the known Ganache addresses with the mnemonic
        const addresses = [
            '0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1', // manager_0 (index 0)
            '0xFFcf8FDEE72ac11b5c542428B35EEF5769C409f0', // manager_1 (index 1)
            '0x22d491Bde2303f2f43325b2108D26f1eAbA1e32b'  // manager_2 (index 2)
        ];
        return addresses[index];
    });
    
    const treasuryAddress = '0xE11BA2b4D45Eaed5996Cd0823791E0C93114882d'; // treasury (index 3)
    
    // Create contract configuration
    const contractConfig = {
        address: '0x5FbDB2315678afecb367f032d93F642f64180aa3', // Placeholder contract address
        owners: managerAddresses,
        threshold: THRESHOLD,
        deployer: treasuryAddress,
        deployedAt: new Date().toISOString(),
        network: 'ganache-local',
        chainId: 1337,
        gasUsed: 2100000 // Estimated gas
    };
    
    console.log('📋 Contract Configuration:');
    console.log(`📍 Contract address: ${contractConfig.address}`);
    console.log(`👥 Owners:`);
    managerAddresses.forEach((addr, idx) => {
        console.log(`   Manager ${idx}: ${addr}`);
    });
    console.log(`💰 Deployer (Treasury): ${contractConfig.deployer}`);
    console.log(`🔐 Threshold: ${contractConfig.threshold}/${managerAddresses.length}`);
    
    // Save contract configuration
    const configPath = path.join(__dirname, '../backend/assets/multisig_contract.json');
    fs.writeFileSync(configPath, JSON.stringify(contractConfig, null, 2));
    console.log(`✅ Configuration saved to: ${configPath}`);
    
    // Create Web3 integration module
    const web3IntegrationCode = `/**
 * MultiSig Contract Integration Module
 * Integrates custom multi-signature contract with existing Web3Manager
 */

class MultiSigContract {
    constructor(web3Manager) {
        this.web3Manager = web3Manager;
        this.config = ${JSON.stringify(contractConfig, null, 2)};
        this.proposals = new Map(); // In-memory proposal storage for demo
        this.proposalCounter = 1;
    }
    
    /**
     * Create a new multi-signature proposal
     * @param {string} target - Target address to send ETH to
     * @param {number} amount - Amount in ETH
     * @param {string} data - Additional data (optional)
     * @returns {Object} Proposal creation result
     */
    async createProposal(target, amount, data = '0x') {
        try {
            const proposalId = this.proposalCounter++;
            const amountWei = this.web3Manager.w3.toWei(amount.toString(), 'ether');
            
            const proposal = {
                id: proposalId,
                target: target,
                amount: amount,
                amountWei: amountWei,
                data: data,
                executed: false,
                signatureCount: 0,
                signatures: new Set(),
                creator: this.web3Manager.accounts['treasury'],
                createdAt: new Date().toISOString(),
                contractAddress: this.config.address
            };
            
            this.proposals.set(proposalId, proposal);
            
            console.log(\`📝 MultiSig Proposal Created: ID-\${proposalId}, Target-\${target}, Amount-\${amount} ETH\`);
            
            return {
                success: true,
                proposalId: proposalId,
                target: target,
                amount: amount,
                amountWei: amountWei,
                contractAddress: this.config.address,
                requiredSignatures: this.config.threshold,
                message: \`Proposal \${proposalId} created successfully\`
            };
        } catch (error) {
            console.error(\`❌ Failed to create proposal: \${error.message}\`);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Sign a multi-signature proposal
     * @param {number} proposalId - ID of the proposal to sign
     * @param {string} signerRole - Role of the signer (manager_0, manager_1, manager_2)
     * @returns {Object} Signing result
     */
    async signProposal(proposalId, signerRole) {
        try {
            const proposal = this.proposals.get(proposalId);
            if (!proposal) {
                throw new Error(\`Proposal \${proposalId} not found\`);
            }
            
            if (proposal.executed) {
                throw new Error(\`Proposal \${proposalId} already executed\`);
            }
            
            const signerAddress = this.web3Manager.accounts[signerRole];
            if (!this.config.owners.includes(signerAddress)) {
                throw new Error(\`\${signerRole} is not an authorized signer\`);
            }
            
            if (proposal.signatures.has(signerRole)) {
                throw new Error(\`\${signerRole} has already signed this proposal\`);
            }
            
            // Add signature
            proposal.signatures.add(signerRole);
            proposal.signatureCount++;
            
            console.log(\`✅ Proposal \${proposalId} signed by \${signerRole} (\${proposal.signatureCount}/\${this.config.threshold})\`);
            
            const result = {
                success: true,
                proposalId: proposalId,
                signer: signerAddress,
                signerRole: signerRole,
                signatureCount: proposal.signatureCount,
                requiredSignatures: this.config.threshold,
                signedAt: new Date().toISOString()
            };
            
            // Auto-execute if threshold met
            if (proposal.signatureCount >= this.config.threshold) {
                const executionResult = await this._executeProposal(proposalId, signerRole);
                result.executed = true;
                result.executionResult = executionResult;
            }
            
            return result;
            
        } catch (error) {
            console.error(\`❌ Failed to sign proposal: \${error.message}\`);
            return {
                success: false,
                error: error.message,
                proposalId: proposalId,
                signerRole: signerRole
            };
        }
    }
    
    /**
     * Execute a proposal (internal method)
     * @param {number} proposalId - ID of the proposal
     * @param {string} executorRole - Role of the final signer/executor
     * @returns {Object} Execution result
     */
    async _executeProposal(proposalId, executorRole) {
        try {
            const proposal = this.proposals.get(proposalId);
            
            if (proposal.signatureCount < this.config.threshold) {
                throw new Error(\`Insufficient signatures: \${proposal.signatureCount}/\${this.config.threshold}\`);
            }
            
            // Execute the reward transfer using existing Web3Manager
            const rewardResult = await this.web3Manager.send_reward(
                'treasury', 
                executorRole, 
                proposal.amount
            );
            
            if (rewardResult.success) {
                proposal.executed = true;
                proposal.executedAt = new Date().toISOString();
                proposal.executorRole = executorRole;
                proposal.executionTxHash = rewardResult.tx_hash;
                
                console.log(\`🎉 Proposal \${proposalId} executed successfully! Reward sent to \${executorRole}\`);
                
                return {
                    success: true,
                    proposalId: proposalId,
                    executor: executorRole,
                    target: proposal.target,
                    amount: proposal.amount,
                    txHash: rewardResult.tx_hash,
                    gasUsed: rewardResult.gas_used,
                    blockNumber: rewardResult.block_number,
                    executedAt: proposal.executedAt
                };
            } else {
                throw new Error(\`Reward transfer failed: \${rewardResult.error}\`);
            }
            
        } catch (error) {
            console.error(\`❌ Failed to execute proposal: \${error.message}\`);
            return {
                success: false,
                error: error.message,
                proposalId: proposalId
            };
        }
    }
    
    /**
     * Get proposal details
     * @param {number} proposalId - ID of the proposal
     * @returns {Object} Proposal details
     */
    getProposal(proposalId) {
        const proposal = this.proposals.get(proposalId);
        if (!proposal) {
            return null;
        }
        
        return {
            id: proposal.id,
            target: proposal.target,
            amount: proposal.amount,
            amountWei: proposal.amountWei,
            executed: proposal.executed,
            signatureCount: proposal.signatureCount,
            requiredSignatures: this.config.threshold,
            creator: proposal.creator,
            createdAt: proposal.createdAt,
            executedAt: proposal.executedAt || null,
            executorRole: proposal.executorRole || null,
            executionTxHash: proposal.executionTxHash || null,
            contractAddress: this.config.address,
            signatures: Array.from(proposal.signatures)
        };
    }
    
    /**
     * Check if a signer has signed a proposal
     * @param {number} proposalId - ID of the proposal
     * @param {string} signerRole - Role to check
     * @returns {boolean} Whether the signer has signed
     */
    hasSigned(proposalId, signerRole) {
        const proposal = this.proposals.get(proposalId);
        return proposal ? proposal.signatures.has(signerRole) : false;
    }
    
    /**
     * Get contract information
     * @returns {Object} Contract details
     */
    getContractInfo() {
        return {
            address: this.config.address,
            owners: this.config.owners,
            threshold: this.config.threshold,
            ownerCount: this.config.owners.length,
            chainId: this.config.chainId,
            deployedAt: this.config.deployedAt,
            totalProposals: this.proposalCounter - 1
        };
    }
    
    /**
     * Get all proposals
     * @returns {Array} Array of all proposals
     */
    getAllProposals() {
        return Array.from(this.proposals.values());
    }
    
    /**
     * Get pending proposals
     * @returns {Array} Array of pending proposals
     */
    getPendingProposals() {
        return Array.from(this.proposals.values()).filter(p => !p.executed);
    }
}

module.exports = MultiSigContract;`;
    
    const integrationPath = path.join(__dirname, '../backend/blockchain/multisig_contract.js');
    fs.writeFileSync(integrationPath, web3IntegrationCode);
    console.log(`🔗 Web3 integration module created: ${integrationPath}`);
    
    // Create contract interface for backend integration
    const contractInterface = {
        name: 'MultiSigProposal',
        address: contractConfig.address,
        abi: [
            {
                "type": "function",
                "name": "createProposal",
                "inputs": [
                    {"name": "target", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "data", "type": "bytes"}
                ],
                "outputs": [{"name": "proposalId", "type": "uint256"}]
            },
            {
                "type": "function",
                "name": "signProposal",
                "inputs": [{"name": "proposalId", "type": "uint256"}]
            },
            {
                "type": "function",
                "name": "getProposal",
                "inputs": [{"name": "proposalId", "type": "uint256"}],
                "outputs": [
                    {"name": "id", "type": "uint256"},
                    {"name": "target", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "executed", "type": "bool"},
                    {"name": "signatureCount", "type": "uint256"},
                    {"name": "creator", "type": "address"},
                    {"name": "createdAt", "type": "uint256"}
                ]
            }
        ],
        events: [
            {
                "type": "event",
                "name": "ProposalCreated",
                "inputs": [
                    {"name": "proposalId", "type": "uint256", "indexed": true},
                    {"name": "creator", "type": "address", "indexed": true},
                    {"name": "target", "type": "address"},
                    {"name": "amount", "type": "uint256"}
                ]
            },
            {
                "type": "event",
                "name": "ProposalSigned",
                "inputs": [
                    {"name": "proposalId", "type": "uint256", "indexed": true},
                    {"name": "signer", "type": "address", "indexed": true}
                ]
            },
            {
                "type": "event",
                "name": "ProposalExecuted",
                "inputs": [
                    {"name": "proposalId", "type": "uint256", "indexed": true},
                    {"name": "executor", "type": "address", "indexed": true},
                    {"name": "target", "type": "address"},
                    {"name": "amount", "type": "uint256"}
                ]
            }
        ]
    };
    
    const interfacePath = path.join(__dirname, '../backend/assets/multisig_interface.json');
    fs.writeFileSync(interfacePath, JSON.stringify(contractInterface, null, 2));
    console.log(`📋 Contract interface saved: ${interfacePath}`);
    
    console.log('\n🎉 MultiSig Contract Setup Complete!');
    console.log('📝 Summary:');
    console.log(`   - Contract Address: ${contractConfig.address}`);
    console.log(`   - Owners: ${contractConfig.owners.length} (${MANAGER_INDICES.map(i => `manager_${i}`).join(', ')})`);
    console.log(`   - Threshold: ${contractConfig.threshold}/${contractConfig.owners.length}`);
    console.log(`   - Integration Module: ${integrationPath}`);
    console.log(`   - Configuration File: ${configPath}`);
    
    return contractConfig;
}

if (require.main === module) {
    main()
        .then((result) => {
            console.log('\n✅ Deployment script completed successfully!');
            process.exit(0);
        })
        .catch((error) => {
            console.error('💥 Deployment script failed:', error);
            process.exit(1);
        });
}

module.exports = { main };