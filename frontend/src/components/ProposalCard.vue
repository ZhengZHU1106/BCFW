<template>
  <div class="proposal-card card" :class="cardClass">
    <div class="card-header">
      <div class="proposal-id">
        <span class="id-label">提案 #{{ proposal.id }}</span>
        <span class="status-badge badge" :class="statusClass">
          {{ statusText }}
        </span>
      </div>
      <div class="proposal-time">
        {{ formatTime(proposal.created_at) }}
      </div>
    </div>
    
    <div class="card-body">
      <!-- 威胁信息 -->
      <div class="threat-info">
        <h4 class="threat-title">{{ proposal.threat_type }} 威胁</h4>
        <div class="threat-details">
          <div class="detail-row">
            <span class="label">目标IP：</span>
            <code class="value">{{ proposal.target_ip || '192.168.1.100' }}</code>
          </div>
          <div class="detail-row">
            <span class="label">置信度：</span>
            <span class="value confidence" :class="confidenceClass">
              {{ (proposal.confidence * 100).toFixed(1) }}%
            </span>
          </div>
          <div class="detail-row">
            <span class="label">建议操作：</span>
            <span class="value action">{{ actionText }}</span>
          </div>
        </div>
      </div>
      
      <!-- 多签进度 -->
      <div class="signature-progress">
        <div class="progress-header">
          <span class="progress-title">签名进度</span>
          <span class="progress-count">{{ signedCount }}/{{ requiredSignatures }}</span>
        </div>
        <div class="progress-bar">
          <div 
            class="progress-fill" 
            :style="{ width: progressPercentage + '%' }"
          ></div>
        </div>
      </div>
      
      <!-- 签名者列表 -->
      <div class="signers-list">
        <div class="signers-header">
          <h5>管理员签名状态</h5>
        </div>
        <div class="signers-grid">
          <div 
            v-for="(signer, index) in signers" 
            :key="index"
            class="signer-item"
            :class="{ 'signed': signer.signed }"
          >
            <div class="signer-info">
              <span class="signer-name">{{ signer.name }}</span>
              <span class="signer-address">{{ formatAddress(signer.address) }}</span>
            </div>
            <div class="signer-status">
              <span v-if="signer.signed" class="status-icon signed">✓</span>
              <span v-else class="status-icon pending">○</span>
            </div>
            <div class="signer-action">
              <button 
                v-if="canSign(index)"
                @click="signProposal(index)"
                class="btn btn-primary btn-sm"
                :disabled="signing"
              >
                {{ signing ? '签名中...' : '签名' }}
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="card-actions" v-if="showActions">
        <button 
          v-if="proposal.status === 'pending' && currentRole === 'operator'"
          @click="withdrawProposal"
          class="btn btn-secondary"
          :disabled="withdrawing"
        >
          {{ withdrawing ? '撤回中...' : '撤回提案' }}
        </button>
      </div>
    </div>
    
    <!-- 执行结果 -->
    <div v-if="proposal.status === 'approved'" class="execution-result">
      <div class="result-header">
        <span class="result-icon">✅</span>
        <span class="result-text">提案已批准并执行</span>
      </div>
      <div class="result-details">
        <p>奖励已发送给最终签名者：{{ finalSignerReward }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  proposal: {
    type: Object,
    required: true
  },
  currentRole: {
    type: String,
    default: 'operator'
  }
})

const emit = defineEmits(['sign', 'refresh'])

// 状态
const signing = ref(false)
const withdrawing = ref(false)

// 计算属性
const cardClass = computed(() => {
  return `status-${props.proposal.status}`
})

const statusClass = computed(() => {
  const mapping = {
    'pending': 'badge-warning',
    'approved': 'badge-success',
    'rejected': 'badge-danger'
  }
  return mapping[props.proposal.status] || 'badge-secondary'
})

const statusText = computed(() => {
  const mapping = {
    'pending': '待处理',
    'approved': '已批准',
    'rejected': '已拒绝'
  }
  return mapping[props.proposal.status] || '未知'
})

const confidenceClass = computed(() => {
  const confidence = props.proposal.confidence
  if (confidence >= 0.8) return 'confidence-high'
  if (confidence >= 0.5) return 'confidence-medium'
  return 'confidence-low'
})

const actionText = computed(() => {
  const mapping = {
    'block': '封锁IP',
    'monitor': '监控',
    'alert': '告警'
  }
  return mapping[props.proposal.action] || '处理'
})

const requiredSignatures = computed(() => 2)

const signedCount = computed(() => {
  return signers.value.filter(s => s.signed).length
})

const progressPercentage = computed(() => {
  return (signedCount.value / requiredSignatures.value) * 100
})

const signers = computed(() => {
  const signatures = props.proposal.signatures || []
  return [
    {
      name: 'Manager 0',
      address: '0x742d35Cc6634C0532925a3b8d8C7B7F0E3B9A3A4',
      signed: signatures.includes('manager_0')
    },
    {
      name: 'Manager 1', 
      address: '0x70997970C51812dc3A010C7d01b50e0d17dc79C8',
      signed: signatures.includes('manager_1')
    },
    {
      name: 'Manager 2',
      address: '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC',
      signed: signatures.includes('manager_2')
    }
  ]
})

const finalSignerReward = computed(() => {
  if (props.proposal.final_signer) {
    return `${props.proposal.final_signer} (0.01 ETH)`
  }
  return '未知'
})

const showActions = computed(() => {
  return props.proposal.status === 'pending'
})

// 方法
const canSign = (managerIndex) => {
  return props.currentRole === 'manager' && 
         props.proposal.status === 'pending' && 
         !signers.value[managerIndex].signed
}

const signProposal = async (managerIndex) => {
  if (signing.value) return
  
  signing.value = true
  try {
    await emit('sign', props.proposal.id, managerIndex)
  } finally {
    signing.value = false
  }
}

const withdrawProposal = async () => {
  if (withdrawing.value) return
  
  if (!confirm('确定要撤回此提案吗？')) {
    return
  }
  
  withdrawing.value = true
  try {
    // 这里可以添加撤回提案的API调用
    alert('撤回功能暂未实现')
  } finally {
    withdrawing.value = false
  }
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

const formatAddress = (address) => {
  return `${address.slice(0, 6)}...${address.slice(-4)}`
}
</script>

<style scoped>
.proposal-card {
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.proposal-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.status-pending {
  border-left: 4px solid #ffc107;
}

.status-approved {
  border-left: 4px solid #28a745;
}

.status-rejected {
  border-left: 4px solid #dc3545;
}

.proposal-id {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.id-label {
  font-weight: 600;
  color: #2c3e50;
}

.proposal-time {
  font-size: 0.875rem;
  color: #6c757d;
}

.threat-info {
  margin-bottom: 1.5rem;
}

.threat-title {
  margin: 0 0 1rem 0;
  color: #e74c3c;
  font-size: 1.1rem;
}

.threat-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.detail-row .label {
  font-size: 0.875rem;
  color: #6c757d;
  min-width: 80px;
}

.detail-row .value {
  font-weight: 500;
}

.detail-row .value.confidence.confidence-high {
  color: #dc3545;
}

.detail-row .value.confidence.confidence-medium {
  color: #fd7e14;
}

.detail-row .value.confidence.confidence-low {
  color: #28a745;
}

.detail-row .value.action {
  color: #007bff;
}

.signature-progress {
  margin-bottom: 1.5rem;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.progress-title {
  font-weight: 500;
  color: #2c3e50;
}

.progress-count {
  font-size: 0.875rem;
  color: #6c757d;
}

.progress-bar {
  height: 8px;
  background-color: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: #007bff;
  transition: width 0.3s ease;
}

.signers-list {
  margin-bottom: 1.5rem;
}

.signers-header h5 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1rem;
}

.signers-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.signer-item {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  background-color: #f8f9fa;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.signer-item.signed {
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
}

.signer-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.signer-name {
  font-weight: 500;
  color: #2c3e50;
}

.signer-address {
  font-size: 0.875rem;
  color: #6c757d;
  font-family: monospace;
}

.signer-status {
  margin-right: 1rem;
}

.status-icon {
  display: inline-block;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  text-align: center;
  line-height: 24px;
  font-weight: bold;
}

.status-icon.signed {
  background-color: #28a745;
  color: white;
}

.status-icon.pending {
  background-color: #6c757d;
  color: white;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.execution-result {
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 4px;
  padding: 1rem;
  margin-top: 1rem;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.result-icon {
  font-size: 1.2rem;
}

.result-text {
  font-weight: 500;
  color: #155724;
}

.result-details {
  font-size: 0.875rem;
  color: #155724;
}

.result-details p {
  margin: 0;
}
</style>