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

    <!-- Reward Pool Dashboard -->
    <div class="reward-pool-section">
      <h3>Reward Pool Management</h3>
      <div class="pool-dashboard-grid">
        <!-- Pool Status Card -->
        <div class="pool-status-card card">
          <div class="card-header">
            <h4 class="card-title">Pool Status</h4>
            <span class="pool-indicator" :class="rewardPoolInfo?.success ? 'active' : 'inactive'">
              {{ rewardPoolInfo?.success ? 'Active' : 'Inactive' }}
            </span>
          </div>
          <div class="pool-stats">
            <div class="stat-item">
              <span class="stat-label">Pool Balance:</span>
              <span class="stat-value">{{ formatBalance(rewardPoolInfo?.balance || 0) }} ETH</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Base Reward:</span>
              <span class="stat-value">{{ formatBalance(rewardPoolInfo?.base_reward || 0.01) }} ETH</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Treasury Balance:</span>
              <span class="stat-value">{{ formatBalance(rewardPoolInfo?.treasury_balance || 0) }} ETH</span>
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

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useSystemStore } from '@/stores/systemStore'
import { useUserStore } from '@/stores/userStore'
import { useThreatStore } from '@/stores/threatStore'
import AccountList from '@/components/AccountList.vue'

// 使用 Pinia stores
const systemStore = useSystemStore()
const userStore = useUserStore()
const threatStore = useThreatStore()

// 从 store 中获取响应式数据
const isConnected = computed(() => systemStore.isConnected)
const blockHeight = computed(() => systemStore.blockHeight)
const networkStatus = computed(() => systemStore.networkStatus)
const lastUpdate = computed(() => systemStore.lastUpdate)
const accounts = computed(() => systemStore.accounts)
const rewardPoolInfo = computed(() => systemStore.rewardPoolInfo || { success: false, balance: 0, base_reward: 0.01, treasury_balance: 0 })
const managerContributions = computed(() => systemStore.managerContributions)
const systemLoading = computed(() => systemStore.isLoading)

const isSimulating = computed(() => threatStore.isSimulating)
const canManageAccounts = computed(() => userStore.canManageAccounts)

// 本地组件状态
const depositAmount = ref(0.1)
const isDepositing = ref(false)

// Timer
let statusTimer: number | null = null

// 使用 store 方法替代本地状态管理
const refreshData = async () => {
  await systemStore.initialize()
}

// Deposit to reward pool using store
const depositToPool = async () => {
  if (isDepositing.value || !depositAmount.value) return
  
  isDepositing.value = true
  try {
    await systemStore.depositToRewardPool('treasury', depositAmount.value)
    alert(`Successfully deposited ${depositAmount.value} ETH to reward pool!`)
    depositAmount.value = 0.1 // Reset to default
  } catch (error) {
    alert(`Failed to deposit: ${error.message || 'Unknown error'}`)
  } finally {
    isDepositing.value = false
  }
}

// Simulate attack using store
const simulateAttack = async () => {
  try {
    const data = await threatStore.simulateAttack()
    const threatInfo = data.threat_info
    alert(`Attack simulation successful!\nActual Type: ${threatInfo.true_label}\nConfidence: ${(threatInfo.confidence * 100).toFixed(1)}%\nModel Prediction: ${threatInfo.predicted_class}`)
  } catch (error) {
    alert('Attack simulation failed. Please check backend service.')
  }
}

// 辅助函数
const formatAddress = (address: string | undefined): string => {
  if (!address) return '-'
  return `${address.slice(0, 6)}...${address.slice(-4)}`
}

const formatBalance = (balance: number | null | undefined): string => {
  if (balance === null || balance === undefined) return '0.0000'
  return parseFloat(balance.toString()).toFixed(4)
}

// 计算属性
const poolBalance = computed(() => {
  return rewardPoolInfo?.balance || 0
})

const totalDistributed = computed(() => {
  return rewardPoolInfo?.total_distributed || 0
})

// Lifecycle
onMounted(async () => {
  // 初始化用户角色
  userStore.initializeFromStorage()
  
  // 初始化系统数据
  await refreshData()
  
  // 设置定期刷新
  statusTimer = setInterval(refreshData, 5000)
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