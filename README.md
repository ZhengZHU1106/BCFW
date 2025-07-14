# Blockchain Intelligent Security Platform

A demonstration prototype project that combines AI-based threat detection with blockchain multi-signature decision-making mechanisms and audit capabilities.

## 🚀 Quick Start

### Prerequisites

Ensure you have the following installed:
- **Node.js** (v16 or higher)
- **Python** (v3.8 or higher)
- **npm** or **yarn**

### One-Click Setup (Recommended)

```bash
# 1. Install dependencies
npm install                    # Install project dependencies
cd frontend && npm install     # Install frontend dependencies
cd ..

# 2. Start complete system
./start-phase3.sh             # One-click start all services
```

### Stop All Services

```bash
# Linux/macOS
./stop_services.sh

# Windows
stop_services.bat
```

After startup, access:
- **Frontend Interface**: http://localhost:5173 (English UI)
- **Backend API**: http://localhost:8000  
- **Ganache Blockchain**: http://127.0.0.1:8545

### Manual Startup (Alternative)

```bash
# 1. Start blockchain
npm run start-chain

# 2. Start backend (new terminal)
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# 3. Start frontend (new terminal)
cd frontend
npm run dev
```

## 🔑 System Accounts

**Fixed Mnemonic**: `bulk tonight audit hover toddler orange boost twenty biology flower govern soldier`

- **Manager 0**: 0x69F652A7392F550F60775d5EDb67f3320764cFa6
- **Manager 1**: 0xB524a6B6DA26d9f7eFF56CEF6093e79efe22ccc7  
- **Manager 2**: 0x2DF346b30BaBf5f9b4F50D3CaA6a766C29e355bc
- **Treasury**: 0x60cE111818C7bAD01020e448D7c5C52c255b084a (System treasury account)

## 🧪 Testing & Verification

```bash
# System status
curl http://localhost:8000/api/system/status

# Attack simulation
curl -X POST http://localhost:8000/api/attack/simulate

# Comprehensive testing
./test_phase2_fixed.sh

# Quick verification
npm run test
npm run test-connection
```

## 📁 Project Structure

```
BCFW/
├── backend/              # FastAPI backend application
│   ├── ai_module/        # AI threat detection (Ensemble_Hybrid model)
│   ├── blockchain/       # Web3 blockchain integration
│   ├── database/         # SQLite data persistence
│   ├── app/              # Business logic services
│   ├── assets/           # AI model and data files
│   ├── config.py         # System configuration
│   └── main.py          # Application entry point
├── frontend/            # Vue 3 frontend application (English UI)
│   ├── src/views/       # Main application views
│   ├── src/components/  # Reusable components
│   ├── src/api/         # API client
│   ├── src/utils/       # Web3 utilities
│   └── vite.config.js   # Vite configuration with API proxy
├── test/                # Test files and verification scripts
├── docs/                # Project documentation
├── scripts/             # Training scripts and data processing
├── start-phase3.sh      # Complete system startup script
├── stop_services.sh     # Service shutdown script (Linux/macOS)
├── stop_services.bat    # Service shutdown script (Windows)
└── package.json         # Project configuration and npm scripts
```

## 🎯 Core Features

### AI Threat Detection
- **Real Ensemble_Hybrid Model**: Trained on CIC-IDS2017 dataset with 99.6%+ accuracy
- **12 Threat Categories**: Including rare attack detection
- **Confidence-Based Response**: Tiered response system based on threat confidence levels

### Blockchain Multi-Signature System
- **2/3 Manager Approval**: Proposals require majority manager signatures
- **ETH Incentive System**: Final signer receives 0.01 ETH reward
- **Real Web3 Integration**: Direct integration with Ganache local blockchain

### Frontend Interface (English)
- **Role-Based Access**: Dynamic switching between Operator and Manager views
- **Real-Time Dashboard**: System status, account balances, and quick actions
- **Threat Monitoring**: Attack simulation and real-time threat visualization
- **Proposal Management**: Multi-signature proposal creation and approval
- **Audit History**: Comprehensive logs for detections and executions
- **Account Management**: Real blockchain account creation with secure private key handling

## 🔧 Available Commands

```bash
# Development
npm run test              # Quick verification
npm run test-full         # Comprehensive testing
npm run test-connection   # Test Ganache connection

# Services
npm run start-chain       # Start Ganache CLI
npm run backend          # Start backend service
./start-phase3.sh        # One-click development environment
./stop_services.sh       # Stop all services

# Configuration
npm run ganache-info     # View Ganache configuration
npm run start-chain-desktop  # Desktop setup instructions
```

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

## 🎖️ Development Status

**Phase 1: Environment & Core Configuration** ✅ **Complete**
- ✅ Project structure design and file organization
- ✅ Base configuration file creation
- ✅ AI model file deployment
- ✅ Testing framework establishment
- ✅ Verification scripts passing

**Phase 2: Backend Development** ✅ **Complete**
- ✅ Web3 connection to Ganache
- ✅ AI model loading module (real Ensemble_Hybrid model)
- ✅ Database design and API implementation
- ✅ Multi-signature proposal system
- ✅ Incentive mechanism and ETH transfers
- ✅ Complete threat detection pipeline

**Phase 3: Frontend Development** ✅ **Complete**
- ✅ Vue 3 + Vite frontend framework with English interface
- ✅ Role switcher (Operator/Manager)
- ✅ Account information dashboard with real account creation
- ✅ Threat detection and alert visualization
- ✅ Multi-signature proposal management interface
- ✅ History records and audit log display
- ✅ Complete end-to-end user interface
- ✅ Real Web3 integration with private key management

**Phase 4: Integration Testing & Delivery** ✅ **Complete**
- ✅ End-to-end manual testing
- ✅ User experience optimization
- ✅ Documentation and deployment preparation

## 🔒 Security Features

- **Private Key Security**: Private keys stored only in session storage, not persisted
- **Role-Based Access Control**: Different permissions for Operators and Managers
- **Blockchain Immutability**: All decisions and actions recorded on blockchain
- **Multi-Signature Security**: Prevents single points of failure in decision making
- **Simulation-Based**: No real firewall interaction, safe for demonstration

## 📊 API Endpoints

```bash
POST /api/attack/simulate        # AI threat detection simulation
GET  /api/system/status         # System health and account balances
GET  /api/proposals             # Multi-sig proposal management
POST /api/proposals/{id}/sign   # Manager proposal signing
GET  /api/logs/detections      # Threat detection audit trail
GET  /api/logs/executions      # Response execution logs
POST /api/test/reward          # Test reward sending function
POST /api/accounts/fund        # Fund account from Treasury
```

## 🎭 Demo Usage

1. **Start System**: Run `./start-phase3.sh`
2. **Access Frontend**: Open http://localhost:5173
3. **Switch Roles**: Use role switcher in top navigation
4. **Simulate Attack**: Click "Simulate Attack" button
5. **Monitor Threats**: View real-time detection results
6. **Manage Proposals**: Approve/reject proposals as Manager
7. **Review History**: Check comprehensive audit logs
8. **Create Accounts**: Use Account Manager to create real blockchain accounts

## 🛠️ Technology Stack

- **Backend**: Python FastAPI, SQLite, Web3.py
- **Frontend**: Vue 3, Vite, JavaScript ES6+
- **Blockchain**: Ganache CLI, Ethereum test network
- **AI/ML**: PyTorch, Joblib, CIC-IDS2017 dataset
- **Development**: Node.js, npm, bash scripting

---

**Note**: This is a demonstration prototype for educational and research purposes. The system simulates security responses and does not interact with real network infrastructure.