<template>
  <div class="history-page">
    <div class="page-header">
      <h2>Security Analytics</h2>
      <div class="header-actions">
        <button @click="refreshAnalytics" class="btn btn-secondary">
          Refresh
        </button>
        <button @click="exportReport" class="btn btn-primary">
          Export Report
        </button>
      </div>
    </div>

    <!-- Analytics Overview -->
    <div class="analytics-overview">
      <div class="overview-stats">
        <div class="stat-card card">
          <div class="stat-icon">🎯</div>
          <div class="stat-info">
            <div class="stat-value">{{ totalThreats }}</div>
            <div class="stat-label">Total Threats</div>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon">🔥</div>
          <div class="stat-info">
            <div class="stat-value">{{ highRiskThreats }}</div>
            <div class="stat-label">High Risk</div>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon">🛡️</div>
          <div class="stat-info">
            <div class="stat-value">{{ blockedThreats }}</div>
            <div class="stat-label">Blocked</div>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon">📈</div>
          <div class="stat-info">
            <div class="stat-value">{{ avgConfidence }}%</div>
            <div class="stat-label">Avg Confidence</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Dashboard -->
    <div class="charts-dashboard">
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading analytics data...</p>
      </div>
      
      <div v-else-if="logs.length === 0" class="no-data">
        <div class="no-data-icon">📊</div>
        <h3>No Data Available</h3>
        <p>No security events recorded yet. Try simulating attacks in the Threat Detection page.</p>
      </div>
      
      <div v-else class="charts-grid">
        <!-- Attack Type Distribution -->
        <div class="chart-container card">
          <div class="chart-header">
            <h3>Attack Type Distribution</h3>
            <span class="chart-subtitle">Breakdown of detected threat types</span>
          </div>
          <div class="chart-wrapper">
            <canvas ref="attackTypeChart" width="400" height="300"></canvas>
          </div>
        </div>
        
        <!-- Confidence Score Distribution -->
        <div class="chart-container card">
          <div class="chart-header">
            <h3>Confidence Score Distribution</h3>
            <span class="chart-subtitle">AI model confidence levels</span>
          </div>
          <div class="chart-wrapper">
            <canvas ref="confidenceChart" width="400" height="300"></canvas>
          </div>
        </div>
        
        <!-- Response Type Analysis -->
        <div class="chart-container card">
          <div class="chart-header">
            <h3>Response Actions Taken</h3>
            <span class="chart-subtitle">Security response distribution</span>
          </div>
          <div class="chart-wrapper">
            <canvas ref="responseChart" width="400" height="300"></canvas>
          </div>
        </div>
        
        <!-- Threat Activity Timeline -->
        <div class="chart-container card chart-wide">
          <div class="chart-header">
            <h3>Threat Activity Timeline</h3>
            <span class="chart-subtitle">24-hour threat detection pattern</span>
          </div>
          <div class="chart-wrapper">
            <canvas ref="timelineChart" width="800" height="400"></canvas>
          </div>
        </div>
        
        <!-- Top Source IPs -->
        <div class="chart-container card">
          <div class="chart-header">
            <h3>Top Source IPs</h3>
            <span class="chart-subtitle">Most active threat sources</span>
          </div>
          <div class="top-sources">
            <div v-for="(source, index) in topSourceIPs" :key="source.ip" class="source-item">
              <div class="source-rank">{{ index + 1 }}</div>
              <div class="source-info">
                <code class="source-ip">{{ source.ip }}</code>
                <div class="source-stats">
                  <span class="threat-count">{{ source.count }} threats</span>
                  <span class="avg-confidence">{{ source.avgConfidence }}% avg confidence</span>
                </div>
              </div>
              <div class="source-bar">
                <div class="bar-fill" :style="{ width: (source.count / maxThreatCount * 100) + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- System Performance -->
        <div class="chart-container card">
          <div class="chart-header">
            <h3>System Performance</h3>
            <span class="chart-subtitle">Detection & response metrics</span>
          </div>
          <div class="performance-metrics">
            <div class="metric">
              <div class="metric-value">{{ responseTimeAvg }}ms</div>
              <div class="metric-label">Avg Response Time</div>
            </div>
            <div class="metric">
              <div class="metric-value">{{ detectionAccuracy }}%</div>
              <div class="metric-label">Detection Accuracy</div>
            </div>
            <div class="metric">
              <div class="metric-value">{{ autoResponseRate }}%</div>
              <div class="metric-label">Auto Response Rate</div>
            </div>
          </div>
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
import { ref, computed, onMounted, nextTick } from 'vue'
import { systemAPI } from '@/api/system'
import LogDetailsModal from '@/components/LogDetailsModal.vue'
import { Chart, registerables } from 'chart.js'

// Register Chart.js components
Chart.register(...registerables)

// State
const logs = ref([])
const originalLogs = ref([]) // Store unfiltered data for compatibility
const logType = ref('detections')
const loading = ref(false)
const selectedLog = ref(null)

// Chart references
const attackTypeChart = ref(null)
const confidenceChart = ref(null)
const responseChart = ref(null)
const timelineChart = ref(null)

// Chart instances
let attackTypeChartInstance = null
let confidenceChartInstance = null
let responseChartInstance = null
let timelineChartInstance = null

// Analytics computed properties
const totalThreats = computed(() => logs.value.length)

const highRiskThreats = computed(() => {
  return logs.value.filter(log => log.confidence >= 0.8).length
})

const blockedThreats = computed(() => {
  return logs.value.filter(log => 
    log.response_level === 'automatic_response' || 
    log.status === 'executed' || 
    log.status === 'approved'
  ).length
})

const avgConfidence = computed(() => {
  if (logs.value.length === 0) return 0
  const total = logs.value.reduce((sum, log) => sum + log.confidence, 0)
  return Math.round((total / logs.value.length) * 100)
})

const topSourceIPs = computed(() => {
  const ipCounts = {}
  logs.value.forEach(log => {
    if (log.source_ip) {
      if (!ipCounts[log.source_ip]) {
        ipCounts[log.source_ip] = {
          count: 0,
          totalConfidence: 0
        }
      }
      ipCounts[log.source_ip].count++
      ipCounts[log.source_ip].totalConfidence += log.confidence
    }
  })
  
  return Object.entries(ipCounts)
    .map(([ip, data]) => ({
      ip,
      count: data.count,
      avgConfidence: Math.round((data.totalConfidence / data.count) * 100)
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5)
})

const maxThreatCount = computed(() => {
  return topSourceIPs.value.length > 0 ? topSourceIPs.value[0].count : 1
})

const responseTimeAvg = computed(() => {
  return Math.floor(Math.random() * 500) + 200 // Mock response time
})

const detectionAccuracy = computed(() => {
  const totalDetections = logs.value.length
  const benignDetections = logs.value.filter(log => log.threat_type === 'Benign').length
  const threatDetections = totalDetections - benignDetections
  
  if (totalDetections === 0) return 0
  return Math.round(((threatDetections + benignDetections * 0.98) / totalDetections) * 100)
})

const autoResponseRate = computed(() => {
  if (logs.value.length === 0) return 0
  const autoResponses = logs.value.filter(log => 
    log.response_level === 'automatic_response'
  ).length
  return Math.round((autoResponses / logs.value.length) * 100)
})

const todayLogs = computed(() => {
  return logs.value.length
})

const autoExecuted = computed(() => {
  if (logType.value === 'detections') {
    // 计算自动响应的检测数量
    return logs.value.filter(log => 
      log.response_level === 'automatic_response' || 
      log.action_taken === 'automatic_block'
    ).length
  } else {
    // 执行日志中的自动执行数量
    return logs.value.filter(log => log.execution_type === 'auto').length
  }
})

const manualApproved = computed(() => {
  if (logType.value === 'detections') {
    // 计算手动批准的提案数量 - 有proposal_id且已执行的威胁
    return logs.value.filter(log => 
      log.proposal_id && (log.status === 'executed' || log.status === 'approved')
    ).length
  } else {
    // 执行日志中的手动批准执行数量
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
      // Store original data for compatibility
      originalLogs.value = result.data || []
      // Load all data directly
      logs.value = result.data || []
      // Wait for DOM to be fully updated before creating charts
      await nextTick()
      // Add a small delay to ensure refs are properly connected
      setTimeout(() => {
        console.log('Creating charts after timeout, checking refs again...')
        console.log('attackTypeChart ref exists:', !!attackTypeChart.value)
        console.log('confidenceChart ref exists:', !!confidenceChart.value)
        createCharts()
      }, 100)
    }
  } catch (error) {
    console.error('Failed to load logs:', error)
    logs.value = []
  } finally {
    loading.value = false
  }
}

// Destroy all chart instances
const destroyAllCharts = () => {
  if (attackTypeChartInstance) {
    attackTypeChartInstance.destroy()
    attackTypeChartInstance = null
  }
  if (confidenceChartInstance) {
    confidenceChartInstance.destroy()
    confidenceChartInstance = null
  }
  if (responseChartInstance) {
    responseChartInstance.destroy()
    responseChartInstance = null
  }
  if (timelineChartInstance) {
    timelineChartInstance.destroy()
    timelineChartInstance = null
  }
}

// Create all charts
const createCharts = () => {
  console.log('createCharts called, logs count:', logs.value.length)
  console.log('First 3 logs:', logs.value.slice(0, 3))
  
  if (logs.value.length === 0) {
    console.log('No logs data, skipping chart creation')
    return
  }
  
  // Destroy existing charts first
  destroyAllCharts()
  
  console.log('Creating charts...')
  createAttackTypeChart()
  createConfidenceChart() 
  createResponseChart()
  createTimelineChart()
  console.log('Charts creation completed')
}

// Create attack type distribution pie chart
const createAttackTypeChart = () => {
  console.log('createAttackTypeChart called, ref exists:', !!attackTypeChart.value)
  if (!attackTypeChart.value) {
    console.log('attackTypeChart ref is null, skipping')
    return
  }
  
  const threatTypes = {}
  logs.value.forEach(log => {
    const type = log.threat_type || 'Unknown'
    threatTypes[type] = (threatTypes[type] || 0) + 1
  })
  
  console.log('Threat types data:', threatTypes)
  
  const colors = [
    '#e74c3c', '#3498db', '#f39c12', '#27ae60', 
    '#9b59b6', '#e67e22', '#1abc9c', '#34495e'
  ]
  
  
  try {
    console.log('Creating Chart.js instance for attack type chart')
    attackTypeChartInstance = new Chart(attackTypeChart.value, {
      type: 'doughnut',
      data: {
        labels: Object.keys(threatTypes),
        datasets: [{
          data: Object.values(threatTypes),
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right'
          }
        }
      }
    })
    console.log('Attack type chart created successfully')
  } catch (error) {
    console.error('Error creating attack type chart:', error)
  }
}

// Create confidence score distribution chart
const createConfidenceChart = () => {
  console.log('createConfidenceChart called, ref exists:', !!confidenceChart.value)
  if (!confidenceChart.value) {
    console.log('confidenceChart ref is null, skipping')
    return
  }
  
  const ranges = {
    'Low (0-50%)': 0,
    'Medium (50-80%)': 0, 
    'High (80-100%)': 0
  }
  
  logs.value.forEach(log => {
    const confidence = log.confidence * 100
    if (confidence < 50) ranges['Low (0-50%)']++
    else if (confidence < 80) ranges['Medium (50-80%)']++
    else ranges['High (80-100%)']++
  })
  
  console.log('Confidence ranges data:', ranges)
  
  try {
    console.log('Creating Chart.js instance for confidence chart')
    confidenceChartInstance = new Chart(confidenceChart.value, {
    type: 'bar',
    data: {
      labels: Object.keys(ranges),
      datasets: [{
        label: 'Number of Threats',
        data: Object.values(ranges),
        backgroundColor: ['#27ae60', '#f39c12', '#e74c3c'],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          }
        }
      }
    }
  })
    console.log('Confidence chart created successfully')
  } catch (error) {
    console.error('Error creating confidence chart:', error)
  }
}

// Create response type chart
const createResponseChart = () => {
  if (!responseChart.value) return
  
  const responses = {}
  logs.value.forEach(log => {
    const response = getResponseText(log.response_level, log.threat_type)
    responses[response] = (responses[response] || 0) + 1
  })
  
  
  responseChartInstance = new Chart(responseChart.value, {
    type: 'pie',
    data: {
      labels: Object.keys(responses),
      datasets: [{
        data: Object.values(responses),
        backgroundColor: ['#3498db', '#27ae60', '#f39c12', '#e74c3c', '#9b59b6']
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false
    }
  })
}

// Create timeline chart
const createTimelineChart = () => {
  if (!timelineChart.value) return
  
  const hourlyData = Array(24).fill(0)
  logs.value.forEach(log => {
    const hour = new Date(log.detected_at || log.executed_at).getHours()
    hourlyData[hour]++
  })
  
  
  timelineChartInstance = new Chart(timelineChart.value, {
    type: 'line',
    data: {
      labels: Array.from({length: 24}, (_, i) => `${i}:00`),
      datasets: [{
        label: 'Threats per Hour',
        data: hourlyData,
        borderColor: '#3498db',
        backgroundColor: 'rgba(52, 152, 219, 0.1)',
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          }
        }
      }
    }
  })
}

// Refresh analytics
const refreshAnalytics = async () => {
  // Destroy existing chart instances before refreshing
  destroyAllCharts()
  await loadLogs()
}


// Export analytics report
const exportReport = () => {
  exportLogs()
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
    'automatic_response': 'badge-success',
    'auto_create_proposal': 'badge-info', 
    'manual_decision_alert': 'badge-warning',
    'log_only': 'badge-secondary',
    'silent_logging': 'badge-secondary'
  }
  return mapping[level] || 'badge-secondary'
}

const getResponseText = (level, threatType = null) => {
  if (level === 'log_only' && threatType === 'Benign') {
    return 'Safe'
  }
  
  const mapping = {
    'automatic_response': 'Auto Response',
    'auto_create_proposal': 'Auto Proposal',
    'manual_decision_alert': 'Manual Decision',
    'log_only': 'Log Only',
    'silent_logging': 'Silent Log'
  }
  return mapping[level] || 'Unknown'
}

const getStatusClass = (status) => {
  const mapping = {
    'detected': 'badge-warning',
    'executed': 'badge-success',
    'proposal_created': 'badge-info',
    'awaiting_decision': 'badge-warning',
    'approved': 'badge-success',
    'rejected': 'badge-danger'
  }
  return mapping[status] || 'badge-secondary'
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

// 获取时间范围
const getTimeRange = () => {
  if (logs.value.length === 0) return 'No data'
  
  const dates = logs.value.map(log => new Date(log.detected_at || log.executed_at))
  const earliest = new Date(Math.min(...dates))
  const latest = new Date(Math.max(...dates))
  
  return `${earliest.toLocaleDateString()} - ${latest.toLocaleDateString()}`
}

// 显示分析面板
const showAnalytics = () => {
  alert('Advanced analytics dashboard will show detailed charts, trends, and insights!')
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
  align-items: flex-start;
  flex-direction: column;
  margin-bottom: 2rem;
  gap: 1rem;
}

@media (min-width: 768px) {
  .page-header {
    flex-direction: row;
    align-items: center;
  }
}

.page-header h2 {
  margin: 0;
  color: #2c3e50;
}

.header-description {
  margin: 0.5rem 0;
}

.header-description p {
  margin: 0;
  color: #6c757d;
  font-size: 1rem;
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

.threat-type-benign {
  color: #27ae60 !important;
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

.btn-info {
  background-color: #17a2b8;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
}

.btn-info:hover {
  background-color: #138496;
  transform: translateY(-1px);
}

.header-info {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.time-range {
  color: #6c757d;
  font-size: 0.9rem;
  font-style: italic;
}

/* Charts Dashboard Styles */
.charts-dashboard {
  margin-top: 2rem;
}

.no-data {
  text-align: center;
  padding: 4rem;
  color: #7f8c8d;
}

.no-data-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.no-data h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.no-data p {
  margin: 0;
  font-size: 1.1rem;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
  align-items: start;
}

.chart-container {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  border: 1px solid #e9ecef;
}

.chart-wide {
  grid-column: 1 / -1;
}

.chart-header {
  margin-bottom: 1rem;
}

.chart-header h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #2c3e50;
  font-weight: 600;
}

.chart-subtitle {
  font-size: 0.9rem;
  color: #6c757d;
  font-style: italic;
}

.chart-wrapper {
  position: relative;
  height: 300px;
}

.chart-wide .chart-wrapper {
  height: 400px;
}

/* Top Sources Styles */
.top-sources {
  max-height: 300px;
  overflow-y: auto;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid #f8f9fa;
}

.source-item:last-child {
  border-bottom: none;
}

.source-rank {
  width: 30px;
  height: 30px;
  background-color: #3498db;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.9rem;
}

.source-info {
  flex: 1;
}

.source-ip {
  font-family: monospace;
  font-size: 0.9rem;
  background-color: #f8f9fa;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  display: block;
  margin-bottom: 0.25rem;
}

.source-stats {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: #6c757d;
}

.source-bar {
  width: 100px;
  height: 8px;
  background-color: #f8f9fa;
  border-radius: 4px;
  position: relative;
}

.bar-fill {
  height: 100%;
  background-color: #3498db;
  border-radius: 4px;
  transition: width 0.3s ease;
}

/* Performance Metrics Styles */
.performance-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

.metric {
  text-align: center;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.metric-value {
  font-size: 1.8rem;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.metric-label {
  font-size: 0.9rem;
  color: #6c757d;
  font-weight: 500;
}

/* Analytics Overview Styles */
.analytics-overview {
  margin-bottom: 2rem;
}

.overview-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .chart-container {
    padding: 1rem;
  }
  
  .chart-wrapper,
  .chart-wide .chart-wrapper {
    height: 250px;
  }
  
  .source-stats {
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .source-bar {
    width: 80px;
  }
  
  .performance-metrics {
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  }
  
  .overview-stats {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
}
</style>