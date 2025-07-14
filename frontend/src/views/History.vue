<template>
  <div class="history-page">
    <div class="page-header">
      <h2>History Records</h2>
      <div class="header-actions">
        <select v-model="logType" @change="loadLogs" class="filter-select">
          <option value="detections">Threat Detection Records</option>
          <option value="executions">Response Execution Records</option>
        </select>
        <button @click="loadLogs" class="btn btn-secondary">
          Refresh
        </button>
        <button @click="exportLogs" class="btn btn-primary">
          Export Records
        </button>
      </div>
    </div>

    <!-- Statistics -->
    <div class="history-stats">
      <div class="stats-grid">
        <div class="stat-card card">
          <div class="stat-icon">📊</div>
          <div class="stat-info">
            <div class="stat-value">{{ totalLogs }}</div>
            <div class="stat-label">Total Records</div>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon">🔍</div>
          <div class="stat-info">
            <div class="stat-value">{{ todayLogs }}</div>
            <div class="stat-label">Today's Records</div>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon">⚡</div>
          <div class="stat-info">
            <div class="stat-value">{{ autoExecuted }}</div>
            <div class="stat-label">Auto Executed</div>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon">👥</div>
          <div class="stat-info">
            <div class="stat-value">{{ manualApproved }}</div>
            <div class="stat-label">Manual Approved</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Log List -->
    <div class="logs-container card">
      <div class="card-header">
        <h3 class="card-title">
          {{ logType === 'detections' ? 'Threat Detection Records' : 'Response Execution Records' }}
        </h3>
        <div class="header-info">
          <span class="log-count">Total {{ logs.length }} records</span>
        </div>
      </div>
      
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading...</p>
      </div>
      
      <div v-else-if="logs.length === 0" class="no-logs">
        <p>No records</p>
      </div>
      
      <div v-else class="logs-content">
        <!-- Threat Detection Records -->
        <div v-if="logType === 'detections'" class="detections-table">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Threat Type</th>
                <th>Source IP</th>
                <th>Confidence</th>
                <th>Response Level</th>
                <th>Status</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in logs" :key="log.id">
                <td>{{ formatTime(log.detected_at) }}</td>
                <td>
                  <span class="threat-type">{{ log.threat_type }}</span>
                </td>
                <td>
                  <code class="ip-address">{{ log.source_ip }}</code>
                </td>
                <td>
                  <span class="confidence-badge" :class="getConfidenceClass(log.confidence)">
                    {{ (log.confidence * 100).toFixed(1) }}%
                  </span>
                </td>
                <td>
                  <span class="response-level badge" :class="getResponseClass(log.response_level)">
                    {{ getResponseText(log.response_level) }}
                  </span>
                </td>
                <td>
                  <span class="status-badge badge" :class="getStatusClass(log.status)">
                    {{ getStatusText(log.status) }}
                  </span>
                </td>
                <td>
                  <button @click="showLogDetails(log)" class="btn btn-sm btn-secondary">
                    Details
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <!-- Response Execution Records -->
        <div v-else class="executions-table">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Action Type</th>
                <th>Target IP</th>
                <th>Execution Method</th>
                <th>Executor</th>
                <th>Status</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in logs" :key="log.id">
                <td>{{ formatTime(log.executed_at) }}</td>
                <td>
                  <span class="action-type">{{ log.action }}</span>
                </td>
                <td>
                  <code class="ip-address">{{ log.target_ip }}</code>
                </td>
                <td>
                  <span class="execution-type badge" :class="getExecutionClass(log.execution_type)">
                    {{ getExecutionText(log.execution_type) }}
                  </span>
                </td>
                <td>
                  <span class="executor">{{ log.executor || 'System' }}</span>
                </td>
                <td>
                  <span class="status-badge badge" :class="getExecutionStatusClass(log.status)">
                    {{ getExecutionStatusText(log.status) }}
                  </span>
                </td>
                <td>
                  <button @click="showLogDetails(log)" class="btn btn-sm btn-secondary">
                    Details
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    
    <!-- Log Details Modal -->
    <LogDetailsModal 
      v-if="selectedLog"
      :log="selectedLog"
      :log-type="logType"
      @close="selectedLog = null"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { systemAPI } from '@/api/system'
import LogDetailsModal from '@/components/LogDetailsModal.vue'

// State
const logs = ref([])
const logType = ref('detections')
const loading = ref(false)
const selectedLog = ref(null)

// Computed properties
const totalLogs = computed(() => logs.value.length)

const todayLogs = computed(() => {
  const today = new Date().toDateString()
  return logs.value.filter(log => {
    const logDate = new Date(log.detected_at || log.executed_at).toDateString()
    return logDate === today
  }).length
})

const autoExecuted = computed(() => {
  if (logType.value === 'detections') {
    return logs.value.filter(log => log.response_level === 'auto').length
  } else {
    return logs.value.filter(log => log.execution_type === 'auto').length
  }
})

const manualApproved = computed(() => {
  if (logType.value === 'detections') {
    return logs.value.filter(log => log.status === 'approved').length
  } else {
    return logs.value.filter(log => log.execution_type === 'manual').length
  }
})

// Load logs
const loadLogs = async () => {
  loading.value = true
  try {
    const result = logType.value === 'detections' 
      ? await systemAPI.getDetectionLogs()
      : await systemAPI.getExecutionLogs()
    
    if (result.success) {
      logs.value = result.data
    }
  } catch (error) {
    console.error('Failed to load logs:', error)
  } finally {
    loading.value = false
  }
}

// Export logs
const exportLogs = () => {
  if (logs.value.length === 0) {
    alert('No data to export')
    return
  }
  
  const csvContent = generateCSV()
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `${logType.value}_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}

// Generate CSV content
const generateCSV = () => {
  if (logType.value === 'detections') {
    const headers = ['Time', 'Threat Type', 'Source IP', 'Confidence', 'Response Level', 'Status']
    const rows = logs.value.map(log => [
      formatTime(log.detected_at),
      log.threat_type,
      log.source_ip,
      (log.confidence * 100).toFixed(1) + '%',
      getResponseText(log.response_level),
      getStatusText(log.status)
    ])
    return [headers, ...rows].map(row => row.join(',')).join('\n')
  } else {
    const headers = ['Time', 'Action Type', 'Target IP', 'Execution Method', 'Executor', 'Status']
    const rows = logs.value.map(log => [
      formatTime(log.executed_at),
      log.action,
      log.target_ip,
      getExecutionText(log.execution_type),
      log.executor || 'System',
      getExecutionStatusText(log.status)
    ])
    return [headers, ...rows].map(row => row.join(',')).join('\n')
  }
}

// 显示日志Details
const showLogDetails = (log) => {
  selectedLog.value = log
}

// Style class methods
const getConfidenceClass = (confidence) => {
  if (confidence >= 0.8) return 'confidence-high'
  if (confidence >= 0.5) return 'confidence-medium'
  return 'confidence-low'
}

const getResponseClass = (level) => {
  const mapping = {
    'auto': 'badge-success',
    'auto_proposal': 'badge-info',
    'manual': 'badge-warning',
    'silent': 'badge-secondary'
  }
  return mapping[level] || 'badge-secondary'
}

const getResponseText = (level) => {
  const mapping = {
    'auto': 'Auto Response',
    'auto_proposal': 'Auto Proposal',
    'manual': 'Manual Decision',
    'silent': 'Silent Log'
  }
  return mapping[level] || '未知'
}

const getStatusClass = (status) => {
  const mapping = {
    'detected': 'badge-warning',
    'executed': 'badge-success',
    'proposal_created': 'badge-info',
    'approved': 'badge-success'
  }
  return mapping[status] || 'badge-secondary'
}

const getStatusText = (status) => {
  const mapping = {
    'detected': 'Detected',
    'executed': 'Executed',
    'proposal_created': 'Proposal Created',
    'approved': 'Approved'
  }
  return mapping[status] || 'Unknown'
}

const getExecutionClass = (type) => {
  const mapping = {
    'auto': 'badge-success',
    'manual': 'badge-info'
  }
  return mapping[type] || 'badge-secondary'
}

const getExecutionText = (type) => {
  const mapping = {
    'auto': 'Auto Execution',
    'manual': 'Manual Approval'
  }
  return mapping[type] || 'Unknown'
}

const getExecutionStatusClass = (status) => {
  const mapping = {
    'success': 'badge-success',
    'failed': 'badge-danger',
    'pending': 'badge-warning'
  }
  return mapping[status] || 'badge-secondary'
}

const getExecutionStatusText = (status) => {
  const mapping = {
    'success': 'Success',
    'failed': 'Failed',
    'pending': 'Processing'
  }
  return mapping[status] || 'Unknown'
}

// Format time
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString('en-US')
}

// Lifecycle
onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.history-page {
  padding: 1rem 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-header h2 {
  margin: 0;
  color: #2c3e50;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.filter-select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.history-stats {
  margin-bottom: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
}

.stat-icon {
  font-size: 2rem;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
  border-radius: 50%;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #2c3e50;
}

.stat-label {
  font-size: 0.9rem;
  color: #7f8c8d;
}

.logs-container {
  overflow-x: auto;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.log-count {
  font-size: 0.9rem;
  color: #6c757d;
}

.logs-content table {
  width: 100%;
  border-collapse: collapse;
}

.logs-content th,
.logs-content td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.logs-content th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #495057;
}

.threat-type,
.action-type {
  font-weight: 500;
  color: #e74c3c;
}

.ip-address {
  font-family: monospace;
  font-size: 0.9rem;
  background-color: #f8f9fa;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.confidence-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 600;
}

.confidence-high {
  background-color: #fee;
  color: #e74c3c;
}

.confidence-medium {
  background-color: #fff3cd;
  color: #f39c12;
}

.confidence-low {
  background-color: #d4edda;
  color: #27ae60;
}

.executor {
  font-style: italic;
  color: #6c757d;
}

.no-logs {
  text-align: center;
  padding: 4rem;
  color: #7f8c8d;
}

.no-logs p {
  margin: 0;
  font-size: 1.2rem;
}
</style>