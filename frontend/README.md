# Blockchain Security Platform - Frontend

A modern frontend application built with Vue 3 + Vite, providing comprehensive threat detection, multi-signature proposal management, and audit logging functionality with an **English interface**.

## 🎯 Core Features

### Main Functionality
- **Role Switching**: Support for Operator and Manager role switching
- **System Dashboard**: Real-time display of account information, block height, and system status
- **Threat Detection**: Attack simulation, alert visualization, and confidence analysis
- **Proposal Management**: Multi-signature proposal workflow visualization
- **History Records**: Complete audit logs and data export functionality

### 💳 Account Management
- **Real Account Creation**: Integrated with Web3.js for creating real Ethereum accounts
- **Fund Management**: Transfer funds from Treasury account to new accounts
- **Balance Monitoring**: Real-time display of all account balance changes
- **Private Key Security**: Secure handling with session-only storage

### 📊 Data Visualization
- **Real-time Updates**: Automatic polling of backend API for latest data
- **Responsive Design**: Adaptive to different screen sizes
- **Interactive Charts**: Intuitive display of threat statistics and proposal progress
- **English Interface**: All UI elements, messages, and alerts in English

## 🛠️ Technology Stack

- **Vue 3**: Modern frontend framework with Composition API
- **Vite**: Fast build tool and development server
- **Vue Router**: Single page application routing
- **Axios**: HTTP client for API communication
- **Web3.js**: Ethereum blockchain integration
- **Ethers.js**: Ethereum utility library

## 🚀 Development Guide

### Start Development Server
```bash
npm run dev
```
Runs on http://localhost:5173

### Build for Production
```bash
npm run build
```

### Preview Build Results
```bash
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── api/          # API clients
│   ├── components/   # Reusable components
│   ├── views/        # Page components
│   ├── utils/        # Utility functions (Web3, etc.)
│   ├── assets/       # Static assets
│   ├── router/       # Route configuration
│   ├── App.vue       # Root component
│   └── main.js       # Entry point
├── public/           # Static files
├── index.html        # HTML template
├── vite.config.js    # Vite configuration
└── package.json      # Dependencies
```

## 📱 Page Structure

### 🏠 Dashboard
- System status overview
- Account information panel
- Quick action buttons
- Real account creation and management
- **English interface for all interactions**

### 🔍 Threats
- Threat simulation functionality
- Real-time alert display
- Threat statistics charts
- Detection record listings
- **All alerts and messages in English**

### 📋 Proposals
- Multi-signature proposal listings
- Proposal details and progress tracking
- Manager signature functionality
- Proposal status monitoring
- **Role-based UI with English labels**

### 📊 History
- Threat detection records
- Response execution logs
- Data export functionality
- Detailed audit information
- **Comprehensive English audit trail**

## ⚙️ Configuration

### API Proxy Configuration
```javascript
// vite.config.js
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',  // Fixed IPv4 for compatibility
      changeOrigin: true,
      secure: false
    }
  }
}
```

### Environment Variables
- `VITE_API_BASE_URL`: Backend API base URL
- `VITE_WEB3_RPC_URL`: Blockchain RPC address

## 🔧 Development Notes

1. **Role Permissions**: Different roles see different functionality
2. **Real-time Updates**: Uses timers to keep data synchronized
3. **Error Handling**: Comprehensive error messages and fallback handling
4. **Responsive Design**: Adapts to mobile and desktop interfaces
5. **Security**: Private keys stored only during session
6. **English Interface**: All user-facing text translated from Chinese
7. **Web3 Integration**: Real blockchain account creation and interaction

## 🌐 Backend Integration

Frontend communicates with backend through these APIs:
- `/api/system/status` - System status and account balances
- `/api/attack/simulate` - Attack simulation with AI model
- `/api/proposals` - Proposal management and signing
- `/api/proposals/{id}/sign` - Manager proposal approval
- `/api/logs/detections` - Threat detection audit trail
- `/api/logs/executions` - Response execution logs
- `/api/accounts/fund` - Account funding from Treasury

## 📱 Browser Support

- Chrome >= 88
- Firefox >= 86
- Safari >= 14
- Edge >= 88

Recommended to use the latest version of modern browsers for the best experience.

## 🎭 Demo Usage Flow

1. **Access Application**: Open http://localhost:5173
2. **Role Selection**: Switch between Operator and Manager using top navigation
3. **Dashboard Overview**: View system status and account information
4. **Create Accounts**: Use Account Manager to create real Web3 accounts
5. **Simulate Attacks**: Click "Simulate Attack" for AI threat detection
6. **Monitor Threats**: View real-time threat alerts and statistics
7. **Manage Proposals**: Review and sign proposals (Manager role)
8. **Audit History**: Export and review comprehensive logs

## 🔒 Security Features

- **Session-only Storage**: Private keys not persisted beyond session
- **Role-based Access**: UI adapts based on user role
- **Real Web3 Integration**: Direct blockchain interaction
- **Error Boundaries**: Graceful handling of Web3 connection issues
- **Input Validation**: Client-side validation for all forms

---

**Note**: This frontend provides a complete English interface for the blockchain security platform demonstration prototype.