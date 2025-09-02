<template>
  <div class="dashboard">
    <h2>System Dashboard</h2>
    
    <!-- Security Flow Status -->
    <div class="flow-status-indicator">
      <div class="flow-stages">
        <div 
          v-for="(stage, index) in securityFlowStages" 
          :key="stage.id"
          class="flow-stage"
          :class="{ 
            'stage-active': currentFlowStage === index,
            'stage-completed': index < currentFlowStage,
            'stage-idle': currentFlowStage === 0 && index === 0
          }"
        >
          <div class="stage-dot"></div>
          <span class="stage-label">{{ stage.name }}</span>
          <div v-if="index < securityFlowStages.length - 1" class="stage-connector"></div>
        </div>
      </div>
      <div class="flow-status-text">
        <span class="status-label">Current Status:</span>
        <span class="status-text" :class="`status-${flowStatusClass}`">
          {{ currentFlowStatusText }}
        </span>
      </div>
    </div>
    
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

    <!-- Reward Pool Dashboard -->
    <div class="reward-pool-section">
      <h3>Reward Pool Management</h3>
      <div class="pool-dashboard-grid">
        <!-- Pool Status Card -->
        <div class="pool-status-card card">
          <div class="card-header">
            <h4 class="card-title">Pool Status</h4>
            <span class="pool-indicator" :class="rewardPoolInfo.success ? 'active' : 'inactive'">
              {{ rewardPoolInfo.success ? 'Active' : 'Inactive' }}
            </span>
          </div>
          <div class="pool-stats">
            <div class="stat-item">
              <span class="stat-label">Pool Balance:</span>
              <span class="stat-value">{{ formatBalance(rewardPoolInfo.balance) }} ETH</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Base Reward:</span>
              <span class="stat-value">{{ formatBalance(rewardPoolInfo.base_reward) }} ETH</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Treasury Balance:</span>
              <span class="stat-value">{{ formatBalance(rewardPoolInfo.treasury_balance) }} ETH</span>
            </div>
          </div>
        </div>

        <!-- Manager Contributions Card -->
        <div class="contributions-card card">
          <div class="card-header">
            <h4 class="card-title">Manager Contributions</h4>
            <button @click="refreshContributions" class="btn btn-sm btn-outline">
              Refresh
            </button>
          </div>
          <div class="contributions-list">
            <div v-for="(contrib, managerRole) in managerContributions" :key="managerRole" class="contribution-item">
              <div class="manager-info">
                <span class="manager-name">{{ managerRole.replace('_', ' ').toUpperCase() }}</span>
                <span class="performance-grade" :class="`grade-${contrib.performance_grade.toLowerCase().replace(' ', '-')}`">
                  {{ contrib.performance_grade }}
                </span>
              </div>
              <div class="contrib-stats">
                <span class="signatures">{{ contrib.total_signatures }} signatures</span>
                <span class="quality">{{ contrib.quality_score }}% quality</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Pool Actions Card -->
        <div class="pool-actions-card card">
          <div class="card-header">
            <h4 class="card-title">Pool Actions</h4>
          </div>
          <div class="pool-actions">
            <div class="action-item">
              <label for="deposit-amount">Deposit Amount (ETH):</label>
              <input 
                id="deposit-amount" 
                v-model.number="depositAmount" 
                type="number" 
                step="0.01" 
                min="0.01" 
                class="form-control"
                placeholder="0.10"
              >
              <button @click="depositToPool" class="btn btn-success" :disabled="isDepositing || !depositAmount">
                {{ isDepositing ? 'Depositing...' : 'Deposit to Pool' }}
              </button>
            </div>
            <div class="action-item">
              <p class="auto-distribution-info">
                🤖 Rewards are automatically distributed when proposals are executed
              </p>
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

// Security flow status
const securityFlowStages = ref([
  { id: 'monitoring', name: 'Monitoring' },
  { id: 'detection', name: 'Detection' },
  { id: 'analysis', name: 'Analysis' },
  { id: 'voting', name: 'Voting' },
  { id: 'execution', name: 'Execution' }
])
const currentFlowStage = ref(0) // 0 = idle/monitoring, 1 = detection, etc.
const currentFlowStatusText = ref('System Ready - Monitoring Network')
const flowStatusClass = ref('idle')

// Reward Pool Management
const rewardPoolInfo = ref({
  success: false,
  balance: 0,
  base_reward: 0.01,
  treasury_balance: 0
})
const managerContributions = ref({})
const depositAmount = ref(0.1)
const isDepositing = ref(false)

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
    
    // Fetch reward pool info
    await fetchRewardPoolInfo()
    await fetchManagerContributions()
    
  } catch (error) {
    console.error('Failed to fetch system status:', error)
    console.error('Error details:', error.response?.data || error.message)
    isConnected.value = false
    networkStatus.value = 'Connection Error'
  }
}

// Fetch reward pool information
const fetchRewardPoolInfo = async () => {
  try {
    const result = await systemAPI.getRewardPoolInfo()
    if (result.success) {
      rewardPoolInfo.value = {
        success: true,
        balance: result.pool_info.balance || 0,
        base_reward: result.pool_info.base_reward || 0.01,
        treasury_balance: result.pool_info.treasury_balance || 0
      }
    } else {
      rewardPoolInfo.value.success = false
    }
  } catch (error) {
    console.error('Failed to fetch reward pool info:', error)
    rewardPoolInfo.value.success = false
  }
}

// Fetch manager contributions
const fetchManagerContributions = async () => {
  try {
    const result = await systemAPI.getManagerContributions()
    if (result.success) {
      managerContributions.value = result.contributions || {}
    }
  } catch (error) {
    console.error('Failed to fetch manager contributions:', error)
    managerContributions.value = {}
  }
}

// Refresh contributions manually
const refreshContributions = async () => {
  await fetchManagerContributions()
}

// Deposit to reward pool
const depositToPool = async () => {
  if (isDepositing.value || !depositAmount.value) return
  
  isDepositing.value = true
  try {
    const result = await systemAPI.depositToRewardPool('treasury', depositAmount.value)
    if (result.success) {
      alert(`Successfully deposited ${depositAmount.value} ETH to reward pool!`)
      await fetchRewardPoolInfo()
      depositAmount.value = 0.1 // Reset to default
    } else {
      alert(`Failed to deposit: ${result.error || 'Unknown error'}`)
    }
  } catch (error) {
    console.error('Deposit failed:', error)
    alert('Deposit failed. Please check backend service.')
  } finally {
    isDepositing.value = false
  }
}

// 手动分配功能已移除 - 现在使用自动分配机制

// Simulate attack
const simulateAttack = async () => {
  if (isSimulating.value) return
  
  isSimulating.value = true
  try {
    const response = await systemAPI.simulateAttack()
    if (response.success && response.data) {
      const threatInfo = response.data.threat_info
      alert(`Attack simulation successful!\nActual Type: ${threatInfo.true_label}\nConfidence: ${(threatInfo.confidence * 100).toFixed(1)}%\nModel Prediction: ${threatInfo.predicted_class}`)
    } else {
      throw new Error('Invalid response format')
    }
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
  margin-bottom: 1.5rem;
  color: #2c3e50;
}

/* Security Flow Status Indicator */
.flow-status-indicator {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
}

.flow-stages {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  position: relative;
}

.flow-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  flex: 1;
}

.stage-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #e9ecef;
  border: 2px solid #dee2e6;
  margin-bottom: 0.5rem;
  transition: all 0.3s ease;
}

.flow-stage.stage-idle .stage-dot {
  background: #6c757d;
  border-color: #495057;
}

.flow-stage.stage-active .stage-dot {
  background: #007bff;
  border-color: #0056b3;
  animation: pulse 2s infinite;
}

.flow-stage.stage-completed .stage-dot {
  background: #28a745;
  border-color: #1e7e34;
}

.stage-label {
  font-size: 0.75rem;
  color: #6c757d;
  font-weight: 500;
  text-align: center;
}

.flow-stage.stage-active .stage-label {
  color: #007bff;
  font-weight: 600;
}

.flow-stage.stage-completed .stage-label {
  color: #28a745;
  font-weight: 600;
}

.stage-connector {
  position: absolute;
  top: 6px;
  left: 50%;
  width: calc(100% - 12px);
  height: 2px;
  background: #dee2e6;
  z-index: -1;
  transition: background-color 0.3s ease;
}

.flow-stage.stage-completed .stage-connector {
  background: #28a745;
}

.flow-status-text {
  text-align: center;
  padding-top: 1rem;
  border-top: 1px solid #e9ecef;
}

.status-label {
  font-size: 0.9rem;
  color: #6c757d;
  margin-right: 0.5rem;
}

.status-text {
  font-weight: 600;
  font-size: 0.9rem;
}

.status-text.status-idle {
  color: #6c757d;
}

.status-text.status-active {
  color: #007bff;
}

.status-text.status-completed {
  color: #28a745;
}

.status-text.status-error {
  color: #dc3545;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
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

/* Reward Pool Styles */
.reward-pool-section {
  margin-bottom: 2rem;
}

.reward-pool-section h3 {
  margin-bottom: 1rem;
  color: #2c3e50;
}

.pool-dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1rem;
  margin-bottom: 2rem;
}

@media (max-width: 1024px) {
  .pool-dashboard-grid {
    grid-template-columns: 1fr;
  }
}

.pool-status-card,
.contributions-card,
.pool-actions-card {
  transition: transform 0.2s;
}

.pool-status-card:hover,
.contributions-card:hover,
.pool-actions-card:hover {
  transform: translateY(-2px);
}

.pool-indicator {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;
}

.pool-indicator.active {
  background-color: #d4edda;
  color: #27ae60;
}

.pool-indicator.inactive {
  background-color: #fee;
  color: #e74c3c;
}

.pool-stats {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-size: 0.875rem;
  color: #7f8c8d;
}

.stat-value {
  font-weight: 600;
  color: #2c3e50;
}

.contributions-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.contribution-item {
  padding: 0.75rem;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  background-color: #f8f9fa;
}

.manager-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.manager-name {
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.875rem;
}

.performance-grade {
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.grade-excellent {
  background-color: #d4edda;
  color: #27ae60;
}

.grade-good {
  background-color: #fff3cd;
  color: #856404;
}

.grade-average {
  background-color: #ffeaa7;
  color: #d68910;
}

.grade-needs-improvement {
  background-color: #f8d7da;
  color: #dc3545;
}

.grade-no-activity {
  background-color: #e2e3e5;
  color: #6c757d;
}

.contrib-stats {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
  color: #6c757d;
}

.pool-actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.action-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.action-item label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #495057;
}

.form-control {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.875rem;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

.btn-outline {
  background: transparent;
  border: 1px solid #6c757d;
  color: #6c757d;
}

.btn-outline:hover {
  background-color: #6c757d;
  color: white;
}

.btn-success {
  background-color: #28a745;
  color: white;
  border: 1px solid #28a745;
}

.btn-success:hover:not(:disabled) {
  background-color: #218838;
  border-color: #1e7e34;
}

.btn-info {
  background-color: #17a2b8;
  color: white;
  border: 1px solid #17a2b8;
}

.btn-info:hover:not(:disabled) {
  background-color: #138496;
  border-color: #117a8b;
}

.auto-distribution-info {
  padding: 0.75rem;
  background-color: #e8f5e8;
  border: 1px solid #c3e6c3;
  border-radius: 6px;
  color: #2d5016;
  font-size: 0.875rem;
  text-align: center;
  margin: 0;
}
</style>