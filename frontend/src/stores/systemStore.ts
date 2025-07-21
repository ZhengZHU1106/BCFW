/**
 * 系统状态管理 Store
 * 管理系统状态、账户信息、网络连接等
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { systemAPI } from '@/api/system'

export interface Account {
  name: string
  role: string
  type: 'info' | 'warning' | 'success' | 'danger'
  address: string
  balance: number
}

export interface SystemStatus {
  blockchain: {
    connected: boolean
    blockHeight: number
    chainId: number
  }
  network: {
    is_connected: boolean
    latest_block: number
  }
  accounts: Array<{
    role: string
    address: string
    balance_eth: number
    balance_wei: string
  }>
  multisig: {
    contract_address: string
    threshold: number
    total_proposals: number
  }
  reward_pool: {
    balance: number
    total_distributed: number
  }
}

export interface RewardPoolInfo {
  balance: number
  total_distributed: number
  total_contributions: number
  distribution_count: number
}

export interface ManagerContribution {
  manager_id: string
  total_signatures: number
  avg_response_time: number
  quality_score: number
  contribution_score: number
  total_rewards: number
}

export const useSystemStore = defineStore('system', () => {
  // State
  const systemStatus = ref<SystemStatus | null>(null)
  const accounts = ref<Account[]>([])
  const rewardPoolInfo = ref<RewardPoolInfo | null>(null)
  const managerContributions = ref<ManagerContribution[]>([])
  const isConnected = ref(false)
  const blockHeight = ref(0)
  const networkStatus = ref('Disconnected')
  const lastUpdate = ref('')
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const managerAccounts = computed(() => 
    accounts.value.filter(acc => acc.role.includes('Manager'))
  )

  const treasuryAccount = computed(() => 
    accounts.value.find(acc => acc.role.includes('Treasury'))
  )

  const totalBalance = computed(() => 
    accounts.value.reduce((total, acc) => total + acc.balance, 0)
  )

  const connectionStatus = computed(() => ({
    isConnected: isConnected.value,
    blockHeight: blockHeight.value,
    networkStatus: networkStatus.value,
    lastUpdate: lastUpdate.value
  }))

  // Actions
  const fetchSystemStatus = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await systemAPI.getStatus()
      
      if (response.success && response.data) {
        systemStatus.value = response.data
        
        // 更新连接状态
        isConnected.value = response.data.network?.is_connected || false
        blockHeight.value = response.data.network?.block_number || 0
        networkStatus.value = response.data.network?.is_connected ? 'Connected' : 'Disconnected'
        
        // 更新账户信息
        if (response.data.accounts && Array.isArray(response.data.accounts)) {
          const managerAccounts = response.data.accounts.filter(acc => acc.role.startsWith('manager'))
          const treasuryAccount = response.data.accounts.find(acc => acc.role === 'treasury')
          
          accounts.value = [
            {
              name: 'Manager 0',
              role: 'Manager',
              type: 'info',
              address: managerAccounts[0]?.address || '',
              balance: managerAccounts[0]?.balance_eth || 0
            },
            {
              name: 'Manager 1', 
              role: 'Manager',
              type: 'info',
              address: managerAccounts[1]?.address || '',
              balance: managerAccounts[1]?.balance_eth || 0
            },
            {
              name: 'Manager 2',
              role: 'Manager', 
              type: 'info',
              address: managerAccounts[2]?.address || '',
              balance: managerAccounts[2]?.balance_eth || 0
            },
            {
              name: 'Treasury',
              role: 'System Treasury',
              type: 'warning',
              address: treasuryAccount?.address || '',
              balance: treasuryAccount?.balance_eth || 0
            }
          ]
        }
        
        lastUpdate.value = new Date().toLocaleTimeString('en-US')
      } else {
        throw new Error(response.message || 'Failed to fetch system status')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error occurred'
      isConnected.value = false
      networkStatus.value = 'Connection Error'
      console.error('Failed to fetch system status:', err)
    } finally {
      isLoading.value = false
    }
  }

  const fetchRewardPoolInfo = async () => {
    try {
      const response = await systemAPI.getRewardPoolInfo()
      
      if (response.success && response.data) {
        rewardPoolInfo.value = response.data
      }
    } catch (err) {
      console.error('Failed to fetch reward pool info:', err)
    }
  }

  const fetchManagerContributions = async () => {
    try {
      const response = await systemAPI.getManagerContributions()
      
      if (response.success && response.data) {
        managerContributions.value = response.data
      }
    } catch (err) {
      console.error('Failed to fetch manager contributions:', err)
    }
  }

  const depositToRewardPool = async (fromRole: string, amount: number) => {
    try {
      const response = await systemAPI.depositToRewardPool(fromRole, amount)
      
      if (response.success) {
        // 刷新奖励池信息
        await fetchRewardPoolInfo()
        await fetchManagerContributions()
        
        return response
      } else {
        throw new Error(response.message || 'Deposit failed')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Deposit failed'
      throw err
    }
  }

  const fundAccount = async (toAddress: string, amount: number = 1.0) => {
    try {
      const response = await systemAPI.fundAccount(toAddress, amount)
      
      if (response.success) {
        // 刷新系统状态
        await fetchSystemStatus()
        return response
      } else {
        throw new Error(response.message || 'Account funding failed')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Account funding failed'
      throw err
    }
  }

  const simulateAttack = async () => {
    try {
      const response = await systemAPI.simulateAttack()
      
      if (response.success && response.data) {
        return response.data
      } else {
        throw new Error(response.message || 'Attack simulation failed')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Attack simulation failed'
      throw err
    }
  }

  // 初始化方法
  const initialize = async () => {
    await Promise.all([
      fetchSystemStatus(),
      fetchRewardPoolInfo(),
      fetchManagerContributions()
    ])
  }

  return {
    // State
    systemStatus,
    accounts,
    rewardPoolInfo,
    managerContributions,
    isConnected,
    blockHeight,
    networkStatus,
    lastUpdate,
    isLoading,
    error,
    
    // Getters
    managerAccounts,
    treasuryAccount,
    totalBalance,
    connectionStatus,
    
    // Actions
    fetchSystemStatus,
    fetchRewardPoolInfo,
    fetchManagerContributions,
    depositToRewardPool,
    fundAccount,
    simulateAttack,
    initialize
  }
})