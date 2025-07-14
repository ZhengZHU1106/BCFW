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
            <h4>基本信息</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="label">检测时间：</span>
                <span class="value">{{ formatTime(log.detected_at) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">威胁类型：</span>
                <span class="value threat-type">{{ log.threat_type }}</span>
              </div>
              <div class="detail-item">
                <span class="label">源IP地址：</span>
                <code class="value">{{ log.source_ip }}</code>
              </div>
              <div class="detail-item">
                <span class="label">置信度：</span>
                <span class="value confidence" :class="getConfidenceClass(log.confidence)">
                  {{ (log.confidence * 100).toFixed(1) }}%
                </span>
              </div>
              <div class="detail-item">
                <span class="label">响应级别：</span>
                <span class="value">{{ getResponseText(log.response_level) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">处理状态：</span>
                <span class="value">{{ getStatusText(log.status) }}</span>
              </div>
            </div>
          </div>
          
          <div class="detail-section" v-if="log.features">
            <h4>特征分析</h4>
            <div class="features-grid">
              <div v-for="(value, key) in log.features" :key="key" class="feature-item">
                <span class="feature-name">{{ key }}:</span>
                <span class="feature-value">{{ value }}</span>
              </div>
            </div>
          </div>
          
          <div class="detail-section" v-if="log.raw_data">
            <h4>原始数据</h4>
            <pre class="raw-data">{{ JSON.stringify(log.raw_data, null, 2) }}</pre>
          </div>
        </div>
        
        <!-- 响应执行记录详情 -->
        <div v-else>
          <div class="detail-section">
            <h4>执行信息</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="label">执行时间：</span>
                <span class="value">{{ formatTime(log.executed_at) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">操作类型：</span>
                <span class="value action-type">{{ log.action }}</span>
              </div>
              <div class="detail-item">
                <span class="label">目标IP：</span>
                <code class="value">{{ log.target_ip }}</code>
              </div>
              <div class="detail-item">
                <span class="label">执行方式：</span>
                <span class="value">{{ getExecutionText(log.execution_type) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">执行者：</span>
                <span class="value">{{ log.executor || '系统' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">执行状态：</span>
                <span class="value">{{ getExecutionStatusText(log.status) }}</span>
              </div>
            </div>
          </div>
          
          <div class="detail-section" v-if="log.proposal_id">
            <h4>关联提案</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="label">提案ID：</span>
                <span class="value">#{{ log.proposal_id }}</span>
              </div>
              <div class="detail-item">
                <span class="label">签名者：</span>
                <span class="value">{{ log.signers ? log.signers.join(', ') : '未知' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">最终签名者：</span>
                <span class="value">{{ log.final_signer || '未知' }}</span>
              </div>
            </div>
          </div>
          
          <div class="detail-section" v-if="log.result">
            <h4>执行结果</h4>
            <div class="execution-result">
              <div class="result-status" :class="log.status">
                {{ getExecutionStatusText(log.status) }}
              </div>
              <div class="result-details">
                <p>{{ log.result.message || '操作完成' }}</p>
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
          关闭
        </button>
        <button @click="copyToClipboard" class="btn btn-primary">
          复制详情
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
  return props.logType === 'detections' ? '威胁检测详情' : '响应执行详情'
})

// 复制详情到剪贴板
const copyToClipboard = async () => {
  try {
    const content = JSON.stringify(props.log, null, 2)
    await navigator.clipboard.writeText(content)
    alert('详情已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    alert('复制失败')
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
    'auto': '自动响应',
    'auto_proposal': '自动提案',
    'manual': '手动决策',
    'silent': '静默记录'
  }
  return mapping[level] || '未知'
}

const getStatusText = (status) => {
  const mapping = {
    'detected': '已检测',
    'executed': '已执行',
    'proposal_created': '已创建提案',
    'approved': '已批准'
  }
  return mapping[status] || '未知'
}

const getExecutionText = (type) => {
  const mapping = {
    'auto': '自动执行',
    'manual': '人工批准'
  }
  return mapping[type] || '未知'
}

const getExecutionStatusText = (status) => {
  const mapping = {
    'success': '成功',
    'failed': '失败',
    'pending': '处理中'
  }
  return mapping[status] || '未知'
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