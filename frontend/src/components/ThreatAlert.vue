<template>
  <div class="threat-alert" :class="alertClass">
    <div class="alert-header">
      <div class="alert-icon">
        {{ alertIcon }}
      </div>
      <div class="alert-title">
        <h4>{{ alertTitle }}</h4>
        <p class="alert-time">{{ formatTime(threat.detected_at) }}</p>
      </div>
      <div class="alert-actions">
        <button v-if="showCreateProposal" @click="createProposal" class="btn btn-primary btn-sm">
          Create Proposal
        </button>
      </div>
    </div>
    
    <div class="alert-body">
      <div class="threat-details">
        <div class="detail-item">
          <span class="label">Type:</span>
          <span class="value threat-type">{{ threat.threat_type || threat.predicted_class }}</span>
        </div>
        <div class="detail-item">
          <span class="label">Source IP:</span>
          <code class="value ip-address">{{ threat.source_ip }}</code>
        </div>
        <div class="detail-item">
          <span class="label">Confidence:</span>
          <span class="value confidence" :class="confidenceClass">
            {{ (threat.confidence * 100).toFixed(1) }}%
          </span>
        </div>
        <div class="detail-item">
          <span class="label">Response Level:</span>
          <span class="value response-level badge" :class="responseClass">
            {{ responseText }}
          </span>
        </div>
      </div>
      
      <div class="alert-description">
        <p>{{ alertDescription }}</p>
      </div>
    </div>
    
    <!-- 自动消失倒计时 -->
    <div v-if="autoHide" class="auto-hide-timer">
      <div class="timer-bar" :style="{ width: timerWidth + '%' }"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { systemAPI } from '@/api/system'

const props = defineProps({
  threat: {
    type: Object,
    required: true
  },
  autoHide: {
    type: Boolean,
    default: true
  },
  hideDuration: {
    type: Number,
    default: 10000 // 10秒
  }
})

const emit = defineEmits(['hide', 'proposalCreated'])

// 自动隐藏定时器
const timerWidth = ref(100)
let hideTimer = null
let timerInterval = null

// 计算属性
const alertClass = computed(() => {
  const threatType = props.threat.threat_type || props.threat.true_label
  if (threatType === 'Benign') return 'alert-safe'
  
  const confidence = props.threat.confidence
  if (confidence >= 0.9) return 'alert-critical'
  if (confidence >= 0.8) return 'alert-high'
  if (confidence >= 0.5) return 'alert-medium'
  return 'alert-low'
})

const alertIcon = computed(() => {
  const threatType = props.threat.threat_type || props.threat.true_label
  if (threatType === 'Benign') return '✅'
  
  const confidence = props.threat.confidence
  if (confidence >= 0.9) return '🚨'
  if (confidence >= 0.8) return '🔥'
  if (confidence >= 0.5) return '⚠️'
  return 'ℹ️'
})

const alertTitle = computed(() => {
  const threatType = props.threat.threat_type || props.threat.true_label
  if (threatType === 'Benign') return 'Normal Traffic Detected'
  
  const confidence = props.threat.confidence
  if (confidence >= 0.9) return 'Critical Threat Alert'
  if (confidence >= 0.8) return 'High Risk Threat Detected'
  if (confidence >= 0.5) return 'Medium Threat Detected'
  return 'Low Level Threat Detected'
})

const alertDescription = computed(() => {
  const type = props.threat.threat_type || props.threat.true_label
  
  if (type === 'Benign') {
    return 'Normal network traffic detected, no security action required'
  }
  
  const descriptions = {
    'DDoS': 'Distributed Denial of Service attack detected, may cause service unavailability',
    'Brute Force': 'Brute force attack attempts detected, may compromise account security',
    'SQL Injection': 'SQL injection attack detected, may lead to data breach',
    'XSS': 'Cross-site scripting attack detected, may steal user information',
    'Port Scan': 'Port scanning activity detected, may be reconnaissance before attack',
    'Malware': 'Malware activity detected, may infect system',
    'Phishing': 'Phishing attack detected, may steal user credentials'
  }
  return descriptions[type] || `${type} threat detected, please handle promptly`
})

const confidenceClass = computed(() => {
  const confidence = props.threat.confidence
  if (confidence >= 0.8) return 'confidence-high'
  if (confidence >= 0.5) return 'confidence-medium'
  return 'confidence-low'
})

const responseClass = computed(() => {
  const level = props.threat.response_level
  const mapping = {
    'auto': 'badge-success',
    'auto_proposal': 'badge-info',
    'manual': 'badge-warning',
    'silent': 'badge-secondary'
  }
  return mapping[level] || 'badge-secondary'
})

const responseText = computed(() => {
  const level = props.threat.response_level
  const mapping = {
    'auto': 'Auto Response',
    'auto_proposal': 'Auto Proposal',
    'manual': 'Manual Decision',
    'silent': 'Silent Log'
  }
  return mapping[level] || 'Unknown'
})

const showCreateProposal = computed(() => {
  const userRole = localStorage.getItem('userRole') || 'operator'
  return userRole === 'operator' && 
         props.threat.response_level === 'manual' && 
         props.threat.status === 'detected'
})

// 创建提案
const createProposal = async () => {
  try {
    const result = await systemAPI.createProposal({
      detection_id: props.threat.id,
      action: 'block'
    })
    
    if (result.success) {
      emit('proposalCreated', result.data)
      alert('Proposal created successfully!')
    }
  } catch (error) {
    console.error('Proposal creation failed:', error)
    alert('Proposal creation failed, please try again later')
  }
}

// 格式化时间
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

// 开始自动隐藏倒计时
const startAutoHide = () => {
  if (!props.autoHide) return
  
  const startTime = Date.now()
  
  // 更新进度条
  timerInterval = setInterval(() => {
    const elapsed = Date.now() - startTime
    const remaining = Math.max(0, props.hideDuration - elapsed)
    timerWidth.value = (remaining / props.hideDuration) * 100
    
    if (remaining <= 0) {
      clearInterval(timerInterval)
    }
  }, 100)
  
  // 设置隐藏定时器
  hideTimer = setTimeout(() => {
    emit('hide')
  }, props.hideDuration)
}

// 停止自动隐藏
const stopAutoHide = () => {
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

// 生命周期
onMounted(() => {
  startAutoHide()
})

onUnmounted(() => {
  stopAutoHide()
})
</script>

<style scoped>
.threat-alert {
  border-left: 4px solid;
  border-radius: 8px;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  position: relative;
  animation: alertSlideIn 0.3s ease-out;
}

@keyframes alertSlideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.alert-critical {
  border-left-color: #dc3545;
  background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
}

.alert-high {
  border-left-color: #fd7e14;
  background: linear-gradient(135deg, #fff8f0 0%, #ffffff 100%);
}

.alert-medium {
  border-left-color: #ffc107;
  background: linear-gradient(135deg, #fffbf0 0%, #ffffff 100%);
}

.alert-low {
  border-left-color: #28a745;
  background: linear-gradient(135deg, #f0fff4 0%, #ffffff 100%);
}

.alert-safe {
  border-left-color: #20c997;
  background: linear-gradient(135deg, #e8fffe 0%, #ffffff 100%);
}

.alert-header {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
}

.alert-icon {
  font-size: 2rem;
  margin-right: 1rem;
}

.alert-title {
  flex: 1;
}

.alert-title h4 {
  margin: 0 0 0.25rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
}

.alert-time {
  margin: 0;
  font-size: 0.875rem;
  color: #6c757d;
}

.alert-actions {
  display: flex;
  gap: 0.5rem;
}

.alert-body {
  padding: 1rem;
}

.threat-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.detail-item .label {
  font-size: 0.875rem;
  color: #6c757d;
  font-weight: 500;
}

.detail-item .value {
  font-weight: 600;
}

.threat-type {
  color: #dc3545;
}

.ip-address {
  font-family: monospace;
  font-size: 0.9rem;
  background-color: #f8f9fa;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.confidence.confidence-high {
  color: #dc3545;
}

.confidence.confidence-medium {
  color: #fd7e14;
}

.confidence.confidence-low {
  color: #28a745;
}

.response-level {
  font-size: 0.75rem;
}

.alert-description {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  margin-top: 1rem;
}

.alert-description p {
  margin: 0;
  color: #495057;
  line-height: 1.5;
}

.auto-hide-timer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background-color: rgba(0, 0, 0, 0.1);
}

.timer-bar {
  height: 100%;
  background-color: #007bff;
  transition: width 0.1s linear;
}
</style>