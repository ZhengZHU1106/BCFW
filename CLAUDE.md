# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a blockchain-based intelligent security platform (区块链智能安防平台) demonstration prototype. The project combines AI-based threat detection with blockchain multi-signature decision making and audit capabilities. The system demonstrates the complete flow from threat detection to decentralized decision-making and trusted logging.

**Key Components:**
- AI threat detection using an `Ensemble_Hybrid` model trained on CIC-IDS2017 dataset
- Ganache local blockchain network for development and testing
- Custom multi-signature smart contract for decentralized decision-making
- Simulated security response execution and audit logging

## Project Architecture

### Core Assets (Ready-to-Use)
- `training.ipynb` - Complete model training code and architecture details
- `model.pth`, `scaler.pkl`, `feature_selector.pkl`, `label_encoder.pkl` - Trained model deployment package
- `抽样数据脚本.ipynb` - Script for extracting real attack samples from CIC-IDS2017
- `inference_data.pt` - Pre-generated attack simulation data
- `selected_features.json`, `model_info.json` - Model metadata

### Current Architecture (Phase 4 Complete - Custom MultiSig)
```
backend/
├── ai_module/              # AI threat detection (✅ Complete)
│   └── model_loader.py     # Real Ensemble_Hybrid model + preprocessors
├── blockchain/             # Web3 blockchain integration (✅ Complete)
│   ├── web3_manager.py     # Ganache connection + custom multi-sig
│   └── multisig_contract.py # Custom MultiSig contract integration
├── database/               # SQLite data persistence (✅ Complete)
│   ├── connection.py       # Database setup and sessions
│   └── models.py           # Proposal, ExecutionLog, ThreatDetectionLog
├── app/                    # Business logic services (✅ Complete)
│   └── services.py         # ThreatDetection, Proposal, SystemInfo services
├── assets/                 # Model deployment package (✅ Complete)
│   ├── model_package/      # Real trained model files (joblib compatible)
│   ├── data/              # 230 real attack samples from CIC-IDS2017
│   ├── multisig_contract.json    # MultiSig contract configuration
│   └── multisig_interface.json  # Contract ABI interface
├── main.py                # FastAPI application (✅ Complete)
└── config.py              # System configuration

contracts/                 # Smart contracts (✅ Complete)
└── MultiSigProposal.sol   # Custom multi-signature contract

scripts/                   # Deployment and utility scripts (✅ Complete)
├── deploy_multisig.js     # Full deployment script (requires ethers)
└── deploy_multisig_simple.js # Simple deployment configuration

frontend/                  # Vue 3 + Vite frontend (✅ Complete)
├── src/
│   ├── views/            # Main application views (Dashboard, Threats, Proposals, History)
│   ├── components/       # Reusable components (AccountList, ThreatAlert, ProposalCard, etc.)
│   ├── api/             # API client for backend communication
│   ├── utils/           # Web3 utilities for account creation and balance checking
│   └── router/          # Vue Router configuration
├── vite.config.js       # Vite configuration with API proxy
└── package.json         # Frontend dependencies
```

### System Roles & Accounts
- **System Treasury Account**: High-balance account (1000 ETH) for incentive payments
- **PoA Signer Accounts**: Node-specific accounts for consensus and block production
- **Manager Business Accounts**: Decision-maker accounts for proposal signing (can be same as PoA accounts)
- **Operator**: Front-line users who monitor alerts and manually create proposals for medium-confidence threats
- **Manager**: Senior decision-makers who review and sign proposals

### Core Workflow
1. **Threat Detection**: AI model processes network data and assigns confidence scores
2. **Tiered Response**:
   - High confidence (>0.90): Automatic response
   - Medium-high (0.80-0.90): Automatic proposal creation
   - Medium-low (0.70-0.80): Alert for manual operator decision
   - Low (<0.70): Silent logging
3. **Multi-sig Process**: Proposals require 2/3 Manager signatures for approval via custom smart contract
4. **Incentive System**: Final signer receives 0.01 ETH from treasury automatically upon execution
5. **Execution Simulation**: Security actions logged in database (no real firewall interaction)

## MultiSig Smart Contract Details

The project uses a custom `MultiSigProposal` smart contract written in Solidity for decentralized proposal management:

**Contract Features:**
- **Owners**: 3 Manager accounts (manager_0, manager_1, manager_2) with deterministic addresses
- **Threshold**: 2/3 signatures required for proposal execution
- **Automatic Execution**: Proposals execute automatically when threshold is reached
- **ETH Rewards**: Integrated reward system sending 0.01 ETH to final signer
- **Event Logging**: Complete on-chain audit trail via events

**Key Contract Methods:**
- `createProposal(address target, uint256 amount, bytes data)` - Create new proposal
- `signProposal(uint256 proposalId)` - Sign existing proposal
- `getProposal(uint256 proposalId)` - Retrieve proposal details
- `getContractInfo()` - Get contract configuration

**Integration Architecture:**
```
Traditional DB → MultiSig Contract → Reward Execution
     ↓               ↓                    ↓
Database Logs    Smart Contract      ETH Transfer
                   Events            
```

**Contract Address**: `0x5FbDB2315678afecb367f032d93F642f64180aa3` (Ganache Local)

## AI Model Details

The project uses an `Ensemble_Hybrid` PyTorch model with the following architecture:
- **Input**: 64 selected features from network traffic data
- **Components**: Deep branch, Wide branch, Residual blocks, Self-attention, Feature interaction
- **Output**: 12 threat categories (including "Rare_Attack" for uncommon threats)
- **Performance**: 99.6+ % accuracy on CIC-IDS2017 test set

## Development Commands

**System Management (Phase 8 Complete - Contract-Level Role Separation):**
```bash
# One-click system startup
./start_system.sh        # Start all services (Ganache, Backend, Frontend)

# One-click system shutdown
./stop_system.sh         # Stop all services and clean up

# Manual backend startup (if needed)
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Manual contract deployment (if needed)
node scripts/deploy_multisig_simple.js
```

**Frontend Development (Phase 3 Complete):**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Frontend runs on http://localhost:5173 with API proxy to backend

# Build for production
npm run build
```

**API Endpoints (All Functional):**
```bash
POST /api/attack/simulate        # AI threat detection simulation
GET  /api/system/status         # System health and account balances
GET  /api/proposals             # Multi-sig proposal management
POST /api/proposals/{id}/sign   # Manager proposal signing
GET  /api/logs/detections      # Threat detection audit trail
GET  /api/logs/executions      # Response execution logs
POST /api/test/reward          # Test reward sending function
POST /api/accounts/fund        # Fund account from Treasury

# Reward Pool Management (Phase A Complete)
GET  /api/reward-pool/info      # Get reward pool balance and statistics
GET  /api/reward-pool/contributions  # Get Manager contribution records  
POST /api/reward-pool/deposit   # Deposit ETH to reward pool
POST /api/test/auto-distribute  # Test automatic reward distribution
# Note: Distribution is now automatic on proposal execution
```

**Frontend Features (English Interface):**
- **Dashboard**: System status, account balances, and quick actions
  - **Reward Pool Management**: Pool balance display, Manager contribution tracking, deposit functionality
  - **Real-time Updates**: Live contribution scores and quality ratings
- **Threat Detection**: Real-time threat monitoring with attack simulation
- **Proposals**: Multi-signature proposal management with role-based access
- **History**: Comprehensive audit logs for detections and executions
- **Account Management**: Real Web3 account creation with private key management
- **Role Switching**: Dynamic role switching between Operator and Manager views
- **Real Blockchain Integration**: Direct integration with Ganache for account creation and funding

**Blockchain Environment:**
- Ganache CLI with fixed mnemonic: `bulk tonight audit hover toddler orange boost twenty biology flower govern soldier`
- Deterministic accounts: Manager_0-2 (indices 0-2), Treasury (index 3) 
- Network: `http://127.0.0.1:8545`, 5-second block time
- Alternative: Ganache Desktop with same mnemonic

**Project Status:**
- ✅ Phase 1: Environment and configuration complete
- ✅ Phase 2: Backend development complete and tested
- ✅ Phase 3: Frontend development complete with English interface
- ✅ **Phase 4: Custom MultiSig Contract** - Custom multi-signature smart contract integration complete
- ✅ AI model integration with real preprocessors (joblib-based)
- ✅ Custom multi-signature smart contract with automatic execution
- ✅ Complete threat detection → smart contract → execution → audit workflow
- ✅ Vue 3 + Vite frontend with real Web3 account creation and management
- ✅ **Phase 3.5: UI Internationalization** - All frontend text converted to English
- ✅ **Phase A: Reward Pool Mechanism** - Complete reward pool system with contribution-based distribution
- ✅ **Phase 8: Contract-Level Role Separation** - True decentralized role management with smart contract enforcement

**MultiSig Contract Features (Phase 4 Complete):**
- ✅ Custom Solidity smart contract (`MultiSigProposal.sol`)
- ✅ 2/3 multi-signature threshold with Manager accounts as owners
- ✅ Automatic proposal execution when signature threshold is reached
- ✅ Integrated ETH reward system (0.01 ETH to final signer)
- ✅ Python integration module for seamless backend interaction
- ✅ On-chain audit trail via smart contract events
- ✅ Backward compatibility with existing database-based proposal system

**Phase A Optimizations (Complete):**
- ✅ **Reward Pool Mechanism**: 100 ETH auto-initialized pool with contribution-based distribution
- ✅ **Quality Scoring System**: 0-100 standardized scoring based on response speed (60%) + activity (40%)
- ✅ **Contribution Algorithm**: Signature count (50%) + quality score (50%) for fair reward distribution
- ✅ **Auto-Distribution**: 1 ETH automatically distributed when proposals execute
- ✅ **Gaming Prevention**: Eliminates "final signer" advantage through merit-based rewards

**Phase 8 Achievements (Contract-Level Role Separation):**
- ✅ **Smart Contract Role Management**: Role validation moved to smart contract layer
- ✅ **True Role Separation**: Operators create proposals, Managers sign proposals
- ✅ **Contract-Enforced Permissions**: Smart contract validates all role-based actions
- ✅ **Decentralized Authorization**: No backend dependency for role validation
- ✅ **Enhanced Security**: Role boundaries enforced at blockchain level
- ✅ **MetaMask Ready**: Foundation for external wallet integration

**Known Issues:**
- 🐛 **User Experience Issue**: 5-second wait time after proposal signing due to synchronous reward distribution and blockchain transaction confirmations
- 📝 **Solution Identified**: Asynchronous reward processing + immediate UI feedback (see Phase 9 plan below)

**Remaining Technical Challenges:**
- 🔄 **MetaMask Integration**: Direct user wallet interaction for genuine Web3 experience
- 🔄 **Advanced Role Management**: Dynamic role assignment and management features

## Technical Implementation Details

**Account Management:**
- Fixed mnemonic ensures deterministic account addresses across restarts
- Manager accounts (0-2) used for multi-signature proposal approval (2/3 threshold)
- Treasury account (3) pays 0.01 ETH incentive to final proposal signer
- Web3 integration handles all blockchain interactions via local Ganache

**API Structure (Phase A Complete - Reward Pool System):**
- **AI Integration**: Real Ensemble_Hybrid model with joblib-compatible preprocessors
- **Database**: SQLite with ThreatDetectionLog, Proposal, ExecutionLog models (extended with contract fields)
- **Blockchain**: Web3.py integration with Ganache + custom MultiSig smart contract
- **MultiSig Contract**: Python integration module (`multisig_contract.py`) for seamless interaction
- **Reward Pool System**: Persistent state management with contribution tracking and auto-distribution
- **Services**: ThreatDetectionService, ProposalService, SystemInfoService, RewardPoolService (all fully integrated)
- **Testing**: Comprehensive test suite including reward pool mechanism and contribution tracking

**Threat Detection Confidence Levels:**
- `>0.90`: Automatic response + execution logging
- `0.80-0.90`: Auto-create proposal for Manager approval
- `0.70-0.80`: Alert only, manual proposal creation by Operator
- `<0.70`: Silent background logging

## Next Development Phases: User Experience & Advanced Features

### **Phase 9: User Experience Optimization** (2-3 days) **[PLANNED]**
**Objective**: Eliminate 5-second wait time after proposal signing for better user experience

**Current Problem:**
- Users experience 5-second delay after clicking "Sign" due to synchronous reward distribution
- Multiple blockchain transactions (reward sending + pool distribution) block the UI
- Creates perception of system being slow/unresponsive

**Solution: Asynchronous Processing + Immediate UI Feedback**
- **Stage 1 (Required)**: Asynchronous reward processing + immediate UI response
  - Separate reward distribution from signing workflow  
  - Return success response immediately after signature validation
  - Process rewards in background with error handling
  - **Expected Improvement**: Wait time 5s → <1s

- **Stage 2 (Optional)**: Progress indicators for background operations
  - Visual feedback for ongoing reward transactions
  - Real-time status updates for better transparency

- **Stage 3 (Optional)**: WebSocket real-time updates
  - Eliminate polling, provide instant status updates
  - Better multi-user experience

**Technical Implementation:**
```
Files to modify:
- backend/app/services.py: Modify _execute_approved_proposal() 
- backend/app/background_tasks.py: New async reward processor
- frontend/src/views/Proposals.vue: Immediate UI feedback
```

**Investment vs Impact:**
- **User Experience Improvement**: 90% problem resolution
- **Code Complexity**: Medium (manageable)
- **Maintenance Cost**: Low
- **ROI**: High (core UX issue resolution)

### **Phase 10: MetaMask Integration** (7-10 days) **[FUTURE]**
**Objective**: Enable direct user wallet interaction for genuine Web3 experience

**Key Improvements:**
- Replace backend-controlled transactions with user-signed transactions
- Implement MetaMask wallet connection and account management
- Enable direct smart contract interaction from frontend
- Provide seamless Web3 user experience with fallback options

**Technical Changes:**
- Frontend: Complete Web3 integration with MetaMask connector
- Smart contract: Ensure compatibility with external wallet interactions
- Backend: Add signature verification for MetaMask-signed transactions
- UX: Design intuitive wallet connection and transaction confirmation flows


## Development Guidelines

- **No Model Training**: Use existing trained model files; all simulation uses pre-generated data
- **Security Focus**: This is a defensive security platform - all features should enhance security monitoring and response
- **Simulation-Based**: No real firewall/network device interaction; all responses are simulated and logged
- **Demonstration-Oriented**: UI clearly visualizes the threat detection → decision → response → audit flow
- **Role-Based Access**: Clear separation between Manager and Operator capabilities
- **English Interface**: All user-facing text, error messages, and documentation are in English
- **Real Web3 Integration**: Frontend uses standard 10-account structure and interacts with Ganache
- **Security Best Practices**: Private keys are not persisted beyond session storage for security