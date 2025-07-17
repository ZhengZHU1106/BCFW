// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.8.0 <0.9.0;

/**
 * @title MultiSigProposal
 * @dev Simple multi-signature contract for security proposal approval and reward distribution
 * Designed specifically for the blockchain security platform
 */
contract MultiSigProposal {
    // Events
    event ProposalCreated(uint256 indexed proposalId, address indexed creator, address target, uint256 amount);
    event ProposalSigned(uint256 indexed proposalId, address indexed signer);
    event ProposalExecuted(uint256 indexed proposalId, address indexed executor, address target, uint256 amount);
    event OwnerAdded(address indexed owner);
    event OwnerRemoved(address indexed owner);
    event ThresholdChanged(uint256 threshold);
    event RewardPoolDeposit(address indexed depositor, uint256 amount, uint256 newBalance);
    event RewardDistributed(address indexed recipient, uint256 amount, uint256 remainingPool);
    event ContributionUpdated(address indexed manager, uint256 totalSignatures, uint256 avgResponseTime);
    event RoleAssigned(address indexed user, Role indexed role);
    event RoleRevoked(address indexed user, Role indexed oldRole);

    // Role definitions
    enum Role { NONE, OPERATOR, MANAGER }
    
    // State variables
    mapping(address => bool) public isOwner;
    mapping(address => Role) public userRoles;
    address[] public owners;
    address[] public operators;
    uint256 public threshold;
    uint256 public proposalCount;
    
    // Reward Pool System
    uint256 public rewardPool;
    uint256 public constant BASE_REWARD = 0.01 ether;
    
    struct ContributionRecord {
        uint256 totalSignatures;
        uint256 totalResponseTime;
        uint256 qualityScore;
        uint256 lastSignatureTime;
    }
    
    mapping(address => ContributionRecord) public contributions;
    
    struct Proposal {
        uint256 id;
        address target;
        uint256 amount;
        bytes data;
        bool executed;
        uint256 signatureCount;
        mapping(address => bool) signatures;
        address creator;
        uint256 createdAt;
    }
    
    mapping(uint256 => Proposal) public proposals;
    
    // Modifiers
    modifier onlyOwner() {
        require(isOwner[msg.sender], "Not an owner");
        _;
    }
    
    modifier onlyOperator() {
        require(userRoles[msg.sender] == Role.OPERATOR, "Not an operator");
        _;
    }
    
    modifier onlyManager() {
        require(userRoles[msg.sender] == Role.MANAGER, "Not a manager");
        _;
    }
    
    modifier onlyOperatorOrManager() {
        require(userRoles[msg.sender] == Role.OPERATOR || userRoles[msg.sender] == Role.MANAGER, "Not authorized");
        _;
    }
    
    modifier proposalExists(uint256 proposalId) {
        require(proposalId < proposalCount, "Proposal does not exist");
        _;
    }
    
    modifier notExecuted(uint256 proposalId) {
        require(!proposals[proposalId].executed, "Proposal already executed");
        _;
    }
    
    /**
     * @dev Constructor sets up the initial owners and threshold
     * @param _owners List of initial owners (will be assigned as managers)
     * @param _threshold Number of signatures required for execution
     */
    constructor(address[] memory _owners, uint256 _threshold) {
        require(_owners.length >= _threshold && _threshold > 0, "Invalid threshold");
        
        for (uint256 i = 0; i < _owners.length; i++) {
            address owner = _owners[i];
            require(owner != address(0), "Invalid owner");
            require(!isOwner[owner], "Duplicate owner");
            
            isOwner[owner] = true;
            owners.push(owner);
            userRoles[owner] = Role.MANAGER; // All initial owners are managers
            emit OwnerAdded(owner);
            emit RoleAssigned(owner, Role.MANAGER);
        }
        
        threshold = _threshold;
        emit ThresholdChanged(_threshold);
    }
    
    /**
     * @dev Create a new proposal for multi-signature approval
     * @param target Address to send ETH to (reward recipient)
     * @param amount Amount of ETH to send (in wei)
     * @param data Additional data (for future extensibility)
     * @return proposalId The ID of the created proposal
     */
    function createProposal(
        address target,
        uint256 amount,
        bytes memory data
    ) external onlyOperatorOrManager returns (uint256 proposalId) {
        require(target != address(0), "Invalid target");
        require(address(this).balance >= amount, "Insufficient contract balance");
        
        proposalId = proposalCount++;
        Proposal storage proposal = proposals[proposalId];
        
        proposal.id = proposalId;
        proposal.target = target;
        proposal.amount = amount;
        proposal.data = data;
        proposal.executed = false;
        proposal.signatureCount = 0;
        proposal.creator = msg.sender;
        proposal.createdAt = block.timestamp;
        
        emit ProposalCreated(proposalId, msg.sender, target, amount);
        
        return proposalId;
    }
    
    /**
     * @dev Sign a proposal (only managers can sign)
     * @param proposalId ID of the proposal to sign
     */
    function signProposal(uint256 proposalId) 
        external 
        onlyManager 
        proposalExists(proposalId) 
        notExecuted(proposalId) 
    {
        Proposal storage proposal = proposals[proposalId];
        require(!proposal.signatures[msg.sender], "Already signed");
        
        proposal.signatures[msg.sender] = true;
        proposal.signatureCount++;
        
        // Update contribution record
        _updateContribution(msg.sender, proposal.createdAt);
        
        emit ProposalSigned(proposalId, msg.sender);
        
        // Auto-execute if threshold is met
        if (proposal.signatureCount >= threshold) {
            _executeProposal(proposalId);
        }
    }
    
    /**
     * @dev Execute a proposal (internal function)
     * @param proposalId ID of the proposal to execute
     */
    function _executeProposal(uint256 proposalId) internal {
        Proposal storage proposal = proposals[proposalId];
        require(proposal.signatureCount >= threshold, "Insufficient signatures");
        require(!proposal.executed, "Already executed");
        require(address(this).balance >= proposal.amount, "Insufficient balance");
        
        proposal.executed = true;
        
        // Send ETH to target
        (bool success, ) = proposal.target.call{value: proposal.amount}(proposal.data);
        require(success, "Transaction failed");
        
        // Give immediate base reward to final signer from reward pool
        if (rewardPool >= BASE_REWARD) {
            rewardPool -= BASE_REWARD;
            (bool rewardSuccess, ) = msg.sender.call{value: BASE_REWARD}("");
            if (rewardSuccess) {
                emit RewardDistributed(msg.sender, BASE_REWARD, rewardPool);
            }
        }
        
        emit ProposalExecuted(proposalId, msg.sender, proposal.target, proposal.amount);
    }
    
    /**
     * @dev Get proposal details
     * @param proposalId ID of the proposal
     * @return id Proposal ID
     * @return target Target address
     * @return amount Amount in wei
     * @return executed Whether executed
     * @return signatureCount Number of signatures
     * @return creator Proposal creator
     * @return createdAt Timestamp of creation
     */
    function getProposal(uint256 proposalId) 
        external 
        view 
        proposalExists(proposalId)
        returns (
            uint256 id,
            address target,
            uint256 amount,
            bool executed,
            uint256 signatureCount,
            address creator,
            uint256 createdAt
        ) 
    {
        Proposal storage proposal = proposals[proposalId];
        return (
            proposal.id,
            proposal.target,
            proposal.amount,
            proposal.executed,
            proposal.signatureCount,
            proposal.creator,
            proposal.createdAt
        );
    }
    
    /**
     * @dev Check if an address has signed a proposal
     * @param proposalId ID of the proposal
     * @param owner Address to check
     * @return Whether the address has signed
     */
    function hasSigned(uint256 proposalId, address owner) 
        external 
        view 
        proposalExists(proposalId)
        returns (bool) 
    {
        return proposals[proposalId].signatures[owner];
    }
    
    /**
     * @dev Get all owners
     * @return Array of owner addresses
     */
    function getOwners() external view returns (address[] memory) {
        return owners;
    }
    
    /**
     * @dev Get contract balance
     * @return Balance in wei
     */
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
    
    /**
     * @dev Receive ETH (for funding the contract)
     */
    receive() external payable {}
    
    /**
     * @dev Fallback function
     */
    fallback() external payable {}
    
    /**
     * @dev Add a new owner (requires multi-sig approval)
     * @param newOwner Address of new owner
     */
    function addOwner(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid owner");
        require(!isOwner[newOwner], "Already an owner");
        
        isOwner[newOwner] = true;
        owners.push(newOwner);
        emit OwnerAdded(newOwner);
    }
    
    /**
     * @dev Change the signature threshold (requires multi-sig approval)
     * @param newThreshold New threshold value
     */
    function changeThreshold(uint256 newThreshold) external onlyOwner {
        require(newThreshold > 0 && newThreshold <= owners.length, "Invalid threshold");
        threshold = newThreshold;
        emit ThresholdChanged(newThreshold);
    }
    
    /**
     * @dev Deposit ETH to the reward pool
     */
    function depositToRewardPool() external payable {
        require(msg.value > 0, "Must send ETH");
        rewardPool += msg.value;
        emit RewardPoolDeposit(msg.sender, msg.value, rewardPool);
    }
    
    /**
     * @dev Update contribution record for a manager
     * @param manager Address of the manager
     * @param proposalCreatedAt When the proposal was created
     */
    function _updateContribution(address manager, uint256 proposalCreatedAt) internal {
        ContributionRecord storage record = contributions[manager];
        
        // Update signature count
        record.totalSignatures++;
        
        // Calculate response time (current time - proposal creation time)
        uint256 responseTime = block.timestamp - proposalCreatedAt;
        record.totalResponseTime += responseTime;
        record.lastSignatureTime = block.timestamp;
        
        // Simple quality score: faster response = higher quality
        // Quality score is inverse of average response time (scaled)
        uint256 avgResponseTime = record.totalResponseTime / record.totalSignatures;
        if (avgResponseTime > 0) {
            record.qualityScore = (1 hours * 100) / avgResponseTime; // Scale factor
        }
        
        emit ContributionUpdated(manager, record.totalSignatures, avgResponseTime);
    }
    
    /**
     * @dev Get contribution record for a manager
     * @param manager Address of the manager
     * @return totalSignatures Total number of signatures
     * @return avgResponseTime Average response time in seconds
     * @return qualityScore Quality score (higher = better)
     * @return lastSignatureTime Timestamp of last signature
     */
    function getContribution(address manager) 
        external 
        view 
        returns (
            uint256 totalSignatures,
            uint256 avgResponseTime,
            uint256 qualityScore,
            uint256 lastSignatureTime
        ) 
    {
        ContributionRecord storage record = contributions[manager];
        uint256 avg = record.totalSignatures > 0 ? 
            record.totalResponseTime / record.totalSignatures : 0;
        
        return (
            record.totalSignatures,
            avg,
            record.qualityScore,
            record.lastSignatureTime
        );
    }
    
    /**
     * @dev Get reward pool information
     * @return balance Current reward pool balance
     * @return baseReward Base reward amount
     */
    function getRewardPoolInfo() external view returns (uint256 balance, uint256 baseReward) {
        return (rewardPool, BASE_REWARD);
    }
    
    /**
     * @dev Assign a role to a user (only owner can call)
     * @param user Address of the user
     * @param role Role to assign
     */
    function assignRole(address user, Role role) external onlyOwner {
        require(user != address(0), "Invalid user address");
        
        Role oldRole = userRoles[user];
        userRoles[user] = role;
        
        // Update operators array if assigning/revoking operator role
        if (role == Role.OPERATOR && oldRole != Role.OPERATOR) {
            operators.push(user);
        } else if (role != Role.OPERATOR && oldRole == Role.OPERATOR) {
            // Remove from operators array
            for (uint256 i = 0; i < operators.length; i++) {
                if (operators[i] == user) {
                    operators[i] = operators[operators.length - 1];
                    operators.pop();
                    break;
                }
            }
        }
        
        emit RoleAssigned(user, role);
        if (oldRole != Role.NONE) {
            emit RoleRevoked(user, oldRole);
        }
    }
    
    /**
     * @dev Revoke a user's role (only owner can call)
     * @param user Address of the user
     */
    function revokeRole(address user) external onlyOwner {
        require(user != address(0), "Invalid user address");
        require(userRoles[user] != Role.NONE, "User has no role");
        
        Role oldRole = userRoles[user];
        userRoles[user] = Role.NONE;
        
        // Remove from operators array if was an operator
        if (oldRole == Role.OPERATOR) {
            for (uint256 i = 0; i < operators.length; i++) {
                if (operators[i] == user) {
                    operators[i] = operators[operators.length - 1];
                    operators.pop();
                    break;
                }
            }
        }
        
        emit RoleRevoked(user, oldRole);
    }
    
    /**
     * @dev Get user's role
     * @param user Address of the user
     * @return Role of the user
     */
    function getUserRole(address user) external view returns (Role) {
        return userRoles[user];
    }
    
    /**
     * @dev Get all operators
     * @return Array of operator addresses
     */
    function getOperators() external view returns (address[] memory) {
        return operators;
    }
    
    /**
     * @dev Check if an address is an operator
     * @param user Address to check
     * @return Whether the address is an operator
     */
    function isOperator(address user) external view returns (bool) {
        return userRoles[user] == Role.OPERATOR;
    }
    
    /**
     * @dev Check if an address is a manager
     * @param user Address to check
     * @return Whether the address is a manager
     */
    function isManager(address user) external view returns (bool) {
        return userRoles[user] == Role.MANAGER;
    }
    
    /**
     * @dev Distribute rewards based on contribution (only owner can call)
     * This function can be called periodically to distribute accumulated rewards
     */
    function distributeContributionRewards() external onlyOwner {
        require(rewardPool > 0, "No rewards to distribute");
        
        uint256 totalContributionScore = 0;
        
        // Calculate total contribution score
        for (uint256 i = 0; i < owners.length; i++) {
            address owner = owners[i];
            ContributionRecord storage record = contributions[owner];
            if (record.totalSignatures > 0) {
                // Contribution score combines signature count and quality
                totalContributionScore += record.totalSignatures + (record.qualityScore / 100);
            }
        }
        
        if (totalContributionScore == 0) return;
        
        // Distribute proportionally
        uint256 availableRewards = rewardPool > BASE_REWARD * owners.length ? 
            rewardPool - (BASE_REWARD * owners.length) : 0; // Keep some for base rewards
            
        for (uint256 i = 0; i < owners.length; i++) {
            address owner = owners[i];
            ContributionRecord storage record = contributions[owner];
            
            if (record.totalSignatures > 0) {
                uint256 contributionScore = record.totalSignatures + (record.qualityScore / 100);
                uint256 reward = (availableRewards * contributionScore) / totalContributionScore;
                
                if (reward > 0 && rewardPool >= reward) {
                    rewardPool -= reward;
                    (bool success, ) = owner.call{value: reward}("");
                    if (success) {
                        emit RewardDistributed(owner, reward, rewardPool);
                    }
                }
            }
        }
    }
}