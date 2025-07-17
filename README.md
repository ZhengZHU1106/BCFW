# Blockchain Intelligent Security Platform

A demonstration prototype that combines AI-based threat detection with blockchain multi-signature decision-making and audit capabilities.

## 🚀 Quick Start

### Prerequisites
- **Node.js** (v16 or higher)
- **Python** (v3.8 or higher)
- **npm** or **yarn**

### One-Click System Management

```bash
# Install dependencies
npm install && cd frontend && npm install && cd ..

# Start complete system
./system.sh start

# Check system status
./system.sh status

# Stop all services
./system.sh stop

# Restart system
./system.sh restart
```

### Access Points
- **Frontend Interface**: http://localhost:5173 (English UI)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Ganache Blockchain**: http://127.0.0.1:8545

## 📋 Current Status: Phase 8 Complete

### ✅ **Phase 8: Contract-Level Role Separation** - COMPLETED

**Key Achievements:**
- ✅ **Smart Contract Role Management**: Role validation moved to blockchain layer
- ✅ **True Role Separation**: Operators create proposals, Managers sign proposals
- ✅ **Contract-Enforced Permissions**: Smart contract validates all role-based actions
- ✅ **Decentralized Authorization**: No backend dependency for role validation
- ✅ **Enhanced Security**: Role boundaries enforced at blockchain level
- ✅ **MetaMask Ready**: Foundation for external wallet integration

**Role System:**
- **Operators** (operator_0 to operator_4): Create proposals
- **Managers** (manager_0 to manager_2): Sign proposals  
- **Smart Contract Enforcement**: All permissions validated at blockchain level

### 🎯 Complete System Features

**AI-Powered Threat Detection**
- Real Ensemble_Hybrid model trained on CIC-IDS2017 dataset (99.6% accuracy)
- 12 threat categories with confidence-based response levels
- 230 real attack samples for simulation

**Blockchain Multi-Signature System**
- Custom smart contract with role-based access control
- 2/3 Manager signature requirement with automatic execution
- Contribution-based reward distribution system
- Complete on-chain audit trail

**Web Interface (English)**
- Role-based UI with specific role selection
- Real-time threat monitoring dashboard
- Multi-signature proposal management
- Comprehensive audit logs and history

## 🔑 System Accounts

**Fixed Mnemonic**: `bulk tonight audit hover toddler orange boost twenty biology flower govern soldier`

- **Manager 0**: 0x69F652A7392F550F60775d5EDb67f3320764cFa6
- **Manager 1**: 0xB524a6B6DA26d9f7eFF56CEF6093e79efe22ccc7  
- **Manager 2**: 0x2DF346b30BaBf5f9b4F50D3CaA6a766C29e355bc
- **Treasury**: 0x60cE111818C7bAD01020e448D7c5C52c255b084a

## 🌊 Threat Detection Workflow

1. **AI Analysis**: Ensemble_Hybrid model processes network data
2. **Confidence Assessment**: Assigns confidence scores to detected threats
3. **Tiered Response**:
   - `>0.90`: Automatic response + execution logging
   - `0.80-0.90`: Auto-create proposal for Manager approval  
   - `0.70-0.80`: Alert for manual Operator decision
   - `<0.70`: Silent background logging
4. **Multi-Signature Approval**: Managers review and sign proposals (2/3 threshold)
5. **Execution & Audit**: Actions executed and logged in immutable blockchain records

## 🧪 Testing & Verification

```bash
# System status
./system.sh status

# API testing
curl http://localhost:8000/api/system/status
curl -X POST http://localhost:8000/api/attack/simulate

# Role-based testing
curl -X POST "http://localhost:8000/api/proposals/1/sign?manager_role=manager_0"
```

## 📊 API Endpoints

```bash
POST /api/attack/simulate          # AI threat detection simulation
GET  /api/system/status           # System health and account balances
GET  /api/proposals               # Multi-sig proposal management
POST /api/proposals/{id}/sign     # Manager proposal signing
GET  /api/logs/detections        # Threat detection audit trail
GET  /api/logs/executions        # Response execution logs
GET  /api/reward-pool/info        # Reward pool information
```

## 🎭 Demo Usage

1. **Start System**: `./system.sh start`
2. **Access Frontend**: Open http://localhost:5173
3. **Switch Roles**: Select specific role (manager_0, operator_1, etc.)
4. **Simulate Attack**: Click "Simulate Attack" button
5. **Monitor Threats**: View real-time detection results
6. **Manage Proposals**: Sign proposals as Manager (role-specific)
7. **Review History**: Check comprehensive audit logs

## 📁 Project Structure

```
BCFW/
├── backend/              # FastAPI backend application
│   ├── ai_module/        # AI threat detection (Ensemble_Hybrid model)
│   ├── blockchain/       # Web3 blockchain integration
│   ├── database/         # SQLite data persistence
│   ├── app/              # Business logic services
│   ├── assets/           # AI model and data files
│   └── main.py          # Application entry point
├── frontend/            # Vue 3 frontend application (English UI)
│   ├── src/views/       # Main application views
│   ├── src/components/  # Reusable components
│   └── src/api/         # API client
├── contracts/           # Smart contracts
│   └── MultiSigProposal.sol  # Custom multi-sig contract
├── system.sh           # Unified system management script
└── CLAUDE.md          # Development guide and instructions
```

## 🔮 Development Roadmap

**✅ Completed Phases:**
- Phase 1-4: Core system development and custom MultiSig contract
- Phase A: Reward pool mechanism with contribution-based distribution
- Phase 8: Contract-level role separation with smart contract enforcement

**🚀 Next Phase:**
- **Phase 9: MetaMask Integration** (7-10 days)
  - Direct user wallet interaction
  - External wallet transaction signing
  - Genuine Web3 user experience

## 🛠️ Technology Stack

- **Backend**: Python FastAPI, SQLite, Web3.py
- **Frontend**: Vue 3, Vite, JavaScript ES6+
- **Blockchain**: Ganache CLI, Ethereum test network
- **Smart Contracts**: Solidity with role-based access control
- **AI/ML**: PyTorch, Joblib, CIC-IDS2017 dataset

## 🔒 Security Features

- **Smart Contract Role Validation**: All permissions enforced at blockchain level
- **Multi-Signature Security**: Prevents single points of failure
- **Blockchain Immutability**: All decisions recorded on blockchain
- **Private Key Security**: Session-only storage, not persisted
- **Simulation-Based**: Safe for demonstration, no real infrastructure interaction

---

**Current Status**: ✅ **Phase 8 Complete - Contract-Level Role Separation**  
**Next Milestone**: Phase 9 - MetaMask Integration  
**System Ready**: Fully functional with smart contract-enforced role security

*Note: This is a demonstration prototype for educational and research purposes.*