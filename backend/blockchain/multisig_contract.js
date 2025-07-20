/**
 * MultiSig Contract Integration Module
 * Integrates custom multi-signature contract with existing Web3Manager
 */

class MultiSigContract {
    constructor(web3Manager) {
        this.web3Manager = web3Manager;
        this.config = {
  "address": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
  "owners": [
    "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1",
    "0xFFcf8FDEE72ac11b5c542428B35EEF5769C409f0",
    "0x22d491Bde2303f2f43325b2108D26f1eAbA1e32b"
  ],
  "threshold": 2,
  "deployer": "0xE11BA2b4D45Eaed5996Cd0823791E0C93114882d",
  "deployedAt": "2025-07-20T10:20:44.752Z",
  "network": "ganache-local",
  "chainId": 1337,
  "gasUsed": 2100000
};
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
            
            console.log(`📝 MultiSig Proposal Created: ID-${proposalId}, Target-${target}, Amount-${amount} ETH`);
            
            return {
                success: true,
                proposalId: proposalId,
                target: target,
                amount: amount,
                amountWei: amountWei,
                contractAddress: this.config.address,
                requiredSignatures: this.config.threshold,
                message: `Proposal ${proposalId} created successfully`
            };
        } catch (error) {
            console.error(`❌ Failed to create proposal: ${error.message}`);
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
                throw new Error(`Proposal ${proposalId} not found`);
            }
            
            if (proposal.executed) {
                throw new Error(`Proposal ${proposalId} already executed`);
            }
            
            const signerAddress = this.web3Manager.accounts[signerRole];
            if (!this.config.owners.includes(signerAddress)) {
                throw new Error(`${signerRole} is not an authorized signer`);
            }
            
            if (proposal.signatures.has(signerRole)) {
                throw new Error(`${signerRole} has already signed this proposal`);
            }
            
            // Add signature
            proposal.signatures.add(signerRole);
            proposal.signatureCount++;
            
            console.log(`✅ Proposal ${proposalId} signed by ${signerRole} (${proposal.signatureCount}/${this.config.threshold})`);
            
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
            console.error(`❌ Failed to sign proposal: ${error.message}`);
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
                throw new Error(`Insufficient signatures: ${proposal.signatureCount}/${this.config.threshold}`);
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
                
                console.log(`🎉 Proposal ${proposalId} executed successfully! Reward sent to ${executorRole}`);
                
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
                throw new Error(`Reward transfer failed: ${rewardResult.error}`);
            }
            
        } catch (error) {
            console.error(`❌ Failed to execute proposal: ${error.message}`);
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

module.exports = MultiSigContract;