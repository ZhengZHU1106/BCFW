<template>
  <div class="modal-backdrop" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>{{ modalTitle }}</h3>
        <button @click="$emit('close')" class="close-btn">&times;</button>
      </div>
      
      <div class="modal-body">
        <!-- 威胁检测记录详情 -->
        <div v-if="logType === 'detections'">
          <div class="detail-section">
            <h4>Basic Information</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="label">Detection Time:</span>
                <span class="value">{{ formatTime(log.detected_at) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Threat Type:</span>
                <span class="value threat-type">{{ log.threat_type }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Source IP:</span>
                <code class="value">{{ log.source_ip }}</code>
              </div>
              <div class="detail-item">
                <span class="label">Confidence:</span>
                <span class="value confidence" :class="getConfidenceClass(log.confidence)">
                  {{ (log.confidence * 100).toFixed(1) }}%
                </span>
              </div>
              <div class="detail-item">
                <span class="label">Response Level:</span>
                <span class="value">{{ getResponseText(log.response_level) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Processing Status:</span>
                <span class="value">{{ getStatusText(log.status) }}</span>
              </div>
            </div>
          </div>
          
          <div class="detail-section" v-if="log.features">
            <h4>Feature Analysis</h4>
            <div class="features-grid">
              <div v-for="(value, key) in log.features" :key="key" class="feature-item">
                <span class="feature-name">{{ key }}:</span>
                <span class="feature-value">{{ value }}</span>
              </div>
            </div>
          </div>
          
          <div class="detail-section" v-if="log.raw_data">
            <h4>Raw Data</h4>
            <pre class="raw-data">{{ JSON.stringify(log.raw_data, null, 2) }}</pre>
          </div>
        </div>
        
        <!-- 响应执行记录详情 -->
        <div v-else>
          <div class="detail-section">
            <h4>Execution Information</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="label">Execution Time:</span>
                <span class="value">{{ formatTime(log.executed_at) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Operation Type:</span>
                <span class="value action-type">{{ log.action }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Target IP:</span>
                <code class="value">{{ log.target_ip }}</code>
              </div>
              <div class="detail-item">
                <span class="label">Execution Method:</span>
                <span class="value">{{ getExecutionText(log.execution_type) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Executor:</span>
                <span class="value">{{ log.executor || 'System' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Execution Status:</span>
                <span class="value">{{ getExecutionStatusText(log.status) }}</span>
              </div>
            </div>
          </div>
          
          <div class="detail-section" v-if="log.proposal_id">
            <h4>Related Proposal</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="label">Proposal ID:</span>
                <span class="value">#{{ log.proposal_id }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Signers:</span>
                <span class="value">{{ log.signers ? log.signers.join(', ') : 'Unknown' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Final Signer:</span>
                <span class="value">{{ log.final_signer || 'Unknown' }}</span>
              </div>
            </div>
          </div>
          
          <div class="detail-section" v-if="log.result">
            <h4>Execution Result</h4>
            <div class="execution-result">
              <div class="result-status" :class="log.status">
                {{ getExecutionStatusText(log.status) }}
              </div>
              <div class="result-details">
                <p>{{ log.result.message || 'Operation completed' }}</p>
                <div v-if="log.result.details" class="result-data">
                  <pre>{{ JSON.stringify(log.result.details, null, 2) }}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button @click="$emit('close')" class="btn btn-secondary">
          Close
        </button>
        <button @click="copyToClipboard" class="btn btn-primary">
          Copy Details
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  log: {
    type: Object,
    required: true
  },
  logType: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close'])

// 计算属性
const modalTitle = computed(() => {
  return props.logType === 'detections' ? 'Threat Detection Details' : 'Response Execution Details'
})

// 复制详情到剪贴板
const copyToClipboard = async () => {
  try {
    const content = JSON.stringify(props.log, null, 2)
    await navigator.clipboard.writeText(content)
    alert('Details copied to clipboard')
  } catch (error) {
    console.error('Copy failed:', error)
    alert('Copy failed')
  }
}

// 样式类方法
const getConfidenceClass = (confidence) => {
  if (confidence >= 0.8) return 'confidence-high'
  if (confidence >= 0.5) return 'confidence-medium'
  return 'confidence-low'
}

const getResponseText = (level) => {
  const mapping = {
    'automatic_response': 'Auto Response',
    'auto_create_proposal': 'Auto Proposal',
    'manual_decision_alert': 'Manual Decision',
    'silent_logging': 'Silent Log'
  }
  return mapping[level] || 'Unknown'
}

const getStatusText = (status) => {
  const mapping = {
    'detected': 'Detected',
    'executed': 'Executed',
    'proposal_created': 'Proposal Created',
    'awaiting_decision': 'Awaiting Decision',
    'approved': 'Approved',
    'rejected': 'Rejected'
  }
  return mapping[status] || 'Unknown'
}

const getExecutionText = (type) => {
  const mapping = {
    'auto': 'Auto Execution',
    'manual': 'Manual Approval'
  }
  return mapping[type] || '未知'
}

const getExecutionStatusText = (status) => {
  const mapping = {
    'success': 'Success',
    'failed': 'Failed',
    'pending': 'Processing'
  }
  return mapping[status] || 'Unknown'
}

// 格式化时间
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6c757d;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #2c3e50;
}

.modal-body {
  padding: 1.5rem;
}

.detail-section {
  margin-bottom: 2rem;
}

.detail-section h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 0.5rem;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-item .label {
  font-size: 0.875rem;
  color: #6c757d;
  font-weight: 500;
}

.detail-item .value {
  font-weight: 600;
  color: #2c3e50;
}

.threat-type,
.action-type {
  color: #e74c3c;
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

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.5rem;
}

.feature-item {
  background-color: #f8f9fa;
  padding: 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.feature-name {
  font-weight: 500;
  color: #6c757d;
}

.feature-value {
  color: #2c3e50;
}

.raw-data {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 0.875rem;
  line-height: 1.4;
}

.execution-result {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
}

.result-status {
  font-weight: 600;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  text-align: center;
  margin-bottom: 1rem;
}

.result-status.success {
  background-color: #d4edda;
  color: #155724;
}

.result-status.failed {
  background-color: #f8d7da;
  color: #721c24;
}

.result-status.pending {
  background-color: #fff3cd;
  color: #856404;
}

.result-details p {
  margin: 0 0 1rem 0;
  color: #495057;
}

.result-data {
  background-color: white;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
}

.result-data pre {
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.4;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #e0e0e0;
}
</style>