# Blockchain Intelligent Security Platform

A demonstration prototype combining AI threat detection with blockchain multi-signature decision-making.

## 🚀 Quick Start

### Local Deployment (DevLeChain)

**Prerequisites:**
- DevLeChain blockchain running (see CLAUDE.md for setup)
- Python 3.11+
- Node.js 22+

**Reset demo state (optional, wipes legacy data):**
```bash
./scripts/reset_poa_demo.sh
```

**Initialise PoA chain (first run / after reset):**
```bash
python3 scripts/bootstrap_poa_demo.py
```

**Start the system:**
```bash
# Start all services (DevLeChain + Backend + Frontend)
./system.sh start

# Access the platform
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000/docs
# - DevLeChain RPC: http://127.0.0.1:8545
```

## 🎯 What It Does

**AI Threat Detection**
- HierarchicalTransformerIDS model trained on CIC-IDS2017 dataset
- 99.30% binary accuracy, 98.90% multi-class accuracy
- Detects 6 threat categories (Bot, Brute Force, DDoS, DoS, PortScan, Web Attack)
- Confidence-based automatic/manual response

**Blockchain Multi-Sig**
- Custom smart contract with 2/3 signature requirement
- Deployed on DevLeChain private Ethereum blockchain (Geth 1.10.22)
- Role separation: Operators create proposals, Managers approve
- Automatic execution and on-chain audit trail

**Web Interface** 
- Role-based dashboard (English UI)
- Real-time threat monitoring
- Proposal management and history

## 🔄 How It Works

1. **AI detects threats** → assigns confidence score
2. **High confidence** → auto-response | **Medium** → create proposal
3. **Managers review** → 2/3 signatures required
4. **Auto-execution** → blockchain audit log

## 📋 System Status

✅ **Complete Features:**
- AI threat detection with real trained model
- Custom multi-signature smart contract  
- Role-based access control
- Reward distribution system
- English web interface

## 🔮 TODO / Improvements

- [ ] MetaMask wallet integration
- [ ] Enhanced threat visualization
- [ ] More ML model options
- [ ] Performance optimizations
- [ ] Mobile-responsive UI

## 🛠️ Tech Stack

**Backend:** FastAPI, SQLite, Web3.py
**Frontend:** Vue 3, Vite
**Blockchain:** DevLeChain (Geth 1.10.22), Solidity 0.8.19
**AI/ML:** PyTorch, CIC-IDS2017 dataset

---

For detailed technical documentation, see [CLAUDE.md](CLAUDE.md).
