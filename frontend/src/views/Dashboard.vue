<template>
  <div class="dashboard">
    <h2>System Dashboard</h2>
    
    <!-- System Status Card -->
    <div class="status-card card">
      <div class="card-header">
        <h3 class="card-title">System Status</h3>
        <span class="status-indicator" :class="isConnected ? 'connected' : 'disconnected'">
          {{ isConnected ? 'Connected' : 'Disconnected' }}
        </span>
      </div>
      <div class="status-info">
        <div class="info-item">
          <span class="info-label">Block Height:</span>
          <span class="info-value">{{ blockHeight }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Network Status:</span>
          <span class="info-value">{{ networkStatus }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Last Update:</span>
          <span class="info-value">{{ lastUpdate }}</span>
        </div>
      </div>
    </div>

    <!-- Account Information Dashboard -->
    <div class="accounts-section">
      <h3>Account Information</h3>
      <AccountList />
      <div class="accounts-grid">
        <div v-for="account in accounts" :key="account.address" class="account-card card">
          <div class="account-header">
            <h4>{{ account.name }}</h4>
            <span class="account-role badge" :class="`badge-${account.type}`">
              {{ account.role }}
            </span>
          </div>
          <div class="account-body">
            <div class="address">
              <span class="label">Address:</span>
              <code>{{ formatAddress(account.address) }}</code>
            </div>
            <div class="balance">
              <span class="label">Balance:</span>
              <span class="value">{{ formatBalance(account.balance) }} ETH</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions card">
      <h3 class="card-title">Quick Actions</h3>
      <div class="actions-grid">
        <button @click="simulateAttack" class="btn btn-danger" :disabled="isSimulating">
          {{ isSimulating ? 'Simulating...' : 'Simulate Attack' }}
        </button>
        <router-link to="/proposals" class="btn btn-primary">
          View Proposals
        </router-link>
        <router-link to="/history" class="btn btn-secondary">
          View History
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { systemAPI } from '@/api/system'
import AccountList from '@/components/AccountList.vue'

// System status
const isConnected = ref(false)
const blockHeight = ref(0)
const networkStatus = ref('Checking...')
const lastUpdate = ref('-')

// Account information
const accounts = ref([])

// Attack simulation status
const isSimulating = ref(false)

// Timer
let statusTimer = null

// 获取系统状态
const fetchSystemStatus = async () => {
  try {
    console.log('Fetching system status...')
    const result = await systemAPI.getStatus()
    console.log('API Response:', result)
    
    // Backend response format: {success: true, data: {...}, message: "..."}
    // API client has already extracted response.data, so result is the full response body
    const status = result.data
    
    isConnected.value = status.network?.is_connected || false
    blockHeight.value = status.network?.block_number || 0
    networkStatus.value = status.network?.is_connected ? 'Running' : 'Connection Failed'
    
    // Update account information
    if (status.accounts && Array.isArray(status.accounts)) {
      const managerAccounts = status.accounts.filter(acc => acc.role.startsWith('manager'))
      const treasuryAccount = status.accounts.find(acc => acc.role === 'treasury')
      
      accounts.value = [
        {
          name: 'Manager 0',
          role: 'Manager',
          type: 'info',
          address: managerAccounts[0]?.address,
          balance: managerAccounts[0]?.balance_eth
        },
        {
          name: 'Manager 1',
          role: 'Manager',
          type: 'info',
          address: managerAccounts[1]?.address,
          balance: managerAccounts[1]?.balance_eth
        },
        {
          name: 'Manager 2',
          role: 'Manager',
          type: 'info',
          address: managerAccounts[2]?.address,
          balance: managerAccounts[2]?.balance_eth
        },
        {
          name: 'Treasury',
          role: 'System Treasury',
          type: 'warning',
          address: treasuryAccount?.address,
          balance: treasuryAccount?.balance_eth
        }
      ]
    }
    
    lastUpdate.value = new Date().toLocaleTimeString('en-US')
  } catch (error) {
    console.error('Failed to fetch system status:', error)
    console.error('Error details:', error.response?.data || error.message)
    isConnected.value = false
    networkStatus.value = 'Connection Error'
  }
}

// Simulate attack
const simulateAttack = async () => {
  if (isSimulating.value) return
  
  isSimulating.value = true
  try {
    const result = await systemAPI.simulateAttack()
    alert(`Attack simulation successful!\nType: ${result.threat_type}\nConfidence: ${result.confidence.toFixed(2)}`)
  } catch (error) {
    console.error('Attack simulation failed:', error)
    alert('Attack simulation failed. Please check backend service.')
  } finally {
    isSimulating.value = false
  }
}

// Format address
const formatAddress = (address) => {
  if (!address) return '-'
  return `${address.slice(0, 6)}...${address.slice(-4)}`
}

// Format balance
const formatBalance = (balance) => {
  if (balance === null || balance === undefined) return '0.0000'
  return parseFloat(balance).toFixed(4)
}

// Lifecycle
onMounted(() => {
  fetchSystemStatus()
  // Update status every 5 seconds
  statusTimer = setInterval(fetchSystemStatus, 5000)
})

onUnmounted(() => {
  if (statusTimer) {
    clearInterval(statusTimer)
  }
})
</script>

<style scoped>
.dashboard {
  padding: 1rem 0;
}

.dashboard h2 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.status-card {
  margin-bottom: 2rem;
}

.status-indicator {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;
}

.status-indicator.connected {
  background-color: #d4edda;
  color: #27ae60;
}

.status-indicator.disconnected {
  background-color: #fee;
  color: #e74c3c;
}

.status-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.info-label {
  font-size: 0.875rem;
  color: #7f8c8d;
  margin-bottom: 0.25rem;
}

.info-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
}

.accounts-section {
  margin-bottom: 2rem;
}

.accounts-section h3 {
  margin-bottom: 1rem;
  color: #2c3e50;
}

.accounts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.account-card {
  transition: transform 0.2s;
}

.account-card:hover {
  transform: translateY(-2px);
}

.account-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.account-header h4 {
  margin: 0;
  color: #2c3e50;
}

.account-role {
  font-size: 0.75rem;
}

.account-body .label {
  font-size: 0.875rem;
  color: #7f8c8d;
  margin-right: 0.5rem;
}

.address {
  margin-bottom: 0.5rem;
}

.address code {
  background-color: #f5f5f5;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.875rem;
}

.balance .value {
  font-weight: 600;
  color: #27ae60;
}

.quick-actions {
  margin-bottom: 2rem;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.actions-grid .btn {
  text-decoration: none;
  text-align: center;
}
</style>