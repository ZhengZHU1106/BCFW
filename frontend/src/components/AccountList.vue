<template>
  <div class="account-list-manager">
    <div class="manager-header">
      <h4>Account Manager</h4>
      <p class="manager-note">Create real blockchain accounts (Ganache environment)</p>
    </div>
    
    <div class="manager-controls">
      <button @click="handleCreateNewAccount" class="btn btn-primary btn-sm" :disabled="isCreating">
        {{ isCreating ? 'Creating...' : 'Create New Account' }}
      </button>
      <button @click="refreshAccounts" class="btn btn-secondary btn-sm">
        Refresh List
      </button>
    </div>

    <div v-if="newAccounts.length > 0" class="new-accounts">
      <h5>Newly Created Accounts:</h5>
      <div v-for="account in newAccounts" 
           :key="account.address" 
           class="new-account-item">
        <div class="account-info">
          <span class="account-name">{{ account.name }}</span>
          <code class="account-address">{{ formatAddress(account.address) }}</code>
          <span class="account-balance">{{ account.balance }} ETH</span>
          <span v-if="account.funded" class="badge badge-success">Funded</span>
        </div>
        <div class="account-actions">
          <button 
            v-if="!account.funded" 
            @click="fundAccount(account)" 
            class="btn-fund"
            :disabled="account.funding"
          >
            {{ account.funding ? 'Funding...' : 'Fund 1 ETH' }}
          </button>
          <button @click="copyPrivateKey(account)" class="btn-copy">
            Copy Private Key
          </button>
        </div>
      </div>
      
      <div class="private-keys-note">
        <p>⚠️ Please keep your private keys safe. They will not be viewable after closing the page.</p>
      </div>
    </div>
    
    <div v-else class="no-accounts">
      <p>No new accounts created yet</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { createNewAccount, getAccountBalance, fundAccount as fundAccountAPI } from '@/utils/web3'
import { systemAPI } from '@/api/system'

// Newly created accounts list
const newAccounts = ref([])

// Creation state
const isCreating = ref(false)

// 账户计数器
let accountCounter = 1

// 创建新账户
const handleCreateNewAccount = async () => {
  if (isCreating.value) return
  
  isCreating.value = true
  try {
    // 生成新账户
    const accountData = await createNewAccount()
    
    // 获取初始余额
    const balance = await getAccountBalance(accountData.address)
    
    // 添加到列表
    const newAccount = {
      name: `新账户 ${accountCounter}`,
      address: accountData.address,
      privateKey: accountData.privateKey,
      balance: balance,
      funded: false,
      funding: false
    }
    
    newAccounts.value.push(newAccount)
    accountCounter++
    
    // 保存到sessionStorage（不使用localStorage以保护私钥）
    saveToSessionStorage()
    
  } catch (error) {
    console.error('创建账户失败:', error)
    alert('创建账户失败，请检查Web3连接')
  } finally {
    isCreating.value = false
  }
}

// 给账户充值
const fundAccount = async (account) => {
  if (account.funding) return
  
  account.funding = true
  try {
    // 调用后端API转账
    const result = await systemAPI.fundAccount(account.address, 1.0)
    
    if (result.success) {
      account.balance = result.data.new_balance.toFixed(4)
      account.funded = true
      alert(`成功向 ${account.name} 充值 1 ETH`)
    }
  } catch (error) {
    console.error('充值失败:', error)
    alert('充值失败，请检查Treasury余额')
  } finally {
    account.funding = false
  }
}

// 复制私钥
const copyPrivateKey = async (account) => {
  try {
    await navigator.clipboard.writeText(account.privateKey)
    alert('Private key copied to clipboard. Please keep it safe!')
  } catch (error) {
    console.error('复制失败:', error)
    // 降级方案
    prompt('请手动复制私钥：', account.privateKey)
  }
}

// 刷新账户余额
const refreshAccounts = async () => {
  for (const account of newAccounts.value) {
    try {
      const balance = await getAccountBalance(account.address)
      account.balance = balance
    } catch (error) {
      console.error('刷新余额失败:', error)
    }
  }
}

// 格式化地址
const formatAddress = (address) => {
  if (!address) return '-'
  return `${address.slice(0, 6)}...${address.slice(-4)}`
}

// 保存到sessionStorage
const saveToSessionStorage = () => {
  // 仅保存必要信息，私钥等敏感信息在页面刷新后丢失
  const safeData = newAccounts.value.map(acc => ({
    name: acc.name,
    address: acc.address,
    funded: acc.funded
  }))
  sessionStorage.setItem('newAccounts', JSON.stringify(safeData))
  sessionStorage.setItem('accountCounter', accountCounter.toString())
}

// 从sessionStorage加载
const loadFromSessionStorage = () => {
  const saved = sessionStorage.getItem('newAccounts')
  if (saved) {
    const safeData = JSON.parse(saved)
    // 恢复账户信息（不包括私钥）
    newAccounts.value = safeData.map(acc => ({
      ...acc,
      privateKey: '已清除',
      balance: '0',
      funding: false
    }))
  }
  
  const savedCounter = sessionStorage.getItem('accountCounter')
  if (savedCounter) {
    accountCounter = parseInt(savedCounter)
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadFromSessionStorage()
  // 如果有已保存的账户，刷新余额
  if (newAccounts.value.length > 0) {
    refreshAccounts()
  }
})
</script>

<style scoped>
.account-list-manager {
  background: #f8f9fa;
  border: 2px solid #dee2e6;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.manager-header {
  margin-bottom: 1rem;
}

.manager-header h4 {
  margin: 0 0 0.25rem 0;
  color: #495057;
}

.manager-note {
  font-size: 0.875rem;
  color: #6c757d;
  margin: 0;
}

.manager-controls {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
}

.new-accounts {
  margin-top: 1rem;
}

.new-accounts h5 {
  margin: 0 0 0.75rem 0;
  color: #495057;
}

.new-account-item {
  background: white;
  padding: 1rem;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 0.75rem;
}

.account-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.account-name {
  font-weight: 500;
  color: #495057;
  min-width: 100px;
}

.account-address {
  font-family: monospace;
  font-size: 0.875rem;
  background: #f8f9fa;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  color: #6c757d;
}

.account-balance {
  color: #28a745;
  font-weight: 600;
}

.account-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-fund {
  padding: 0.25rem 0.75rem;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-fund:hover:not(:disabled) {
  background: #218838;
}

.btn-fund:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-copy {
  padding: 0.25rem 0.75rem;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-copy:hover {
  background: #5a6268;
}

.private-keys-note {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 4px;
}

.private-keys-note p {
  margin: 0;
  color: #856404;
  font-size: 0.875rem;
}

.no-accounts {
  text-align: center;
  padding: 2rem;
  color: #6c757d;
}

.no-accounts p {
  margin: 0;
}
</style>