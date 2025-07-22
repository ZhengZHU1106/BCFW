# Blockchain Intelligent Security Platform

A demonstration prototype combining AI threat detection with blockchain multi-signature decision-making.

## 🚀 Quick Start (Recommended)

### Docker Deployment

#### Method 1: Command Line (Recommended)

**Step 1: Pull the image**
```bash
docker pull coderehero/bcfw:v3
```

**Step 2: Run the container (single command)**
```bash
docker run -d -p 5173:5173 -p 8000:8000 -p 8545:8545 --name bcfw coderehero/bcfw:v3
```

**Step 3: Access the platform**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Blockchain RPC: http://localhost:8545

#### Method 2: Docker Desktop GUI

1. **Search and Pull:**
   - Open Docker Desktop
   - Go to "Images" tab
   - Search for `coderehero/bcfw`
   - Click "Pull" on version `v3`

2. **Run Container:**
   - Click "Run" button on the image
   - Click "Optional Settings" dropdown
   - Container name: `bcfw`
   - Port mapping:
     - Host: 5173 → Container: 5173
     - Host: 8000 → Container: 8000  
     - Host: 8545 → Container: 8545
   - Click "Run"

3. **Access:** Same URLs as above

**Container Management:**
```bash
# View logs
docker logs bcfw

# Stop/Start/Remove
docker stop bcfw
docker start bcfw
docker rm bcfw
```

### Local Development

```bash
# Install dependencies
npm install && cd frontend && npm install && cd ..

# Start system
./system.sh start

# Access: http://localhost:5173
```

## 🎯 What It Does

**AI Threat Detection**
- Real ML model trained on CIC-IDS2017 dataset (99.6% accuracy)
- Detects 12 types of network threats
- Confidence-based automatic/manual response

**Blockchain Multi-Sig**
- Custom smart contract with 2/3 signature requirement
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
**Blockchain:** Ganache, Solidity  
**AI/ML:** PyTorch, CIC-IDS2017 dataset

---

**Docker Image:** `coderehero/bcfw:v3` | **Demo Ready** ✅