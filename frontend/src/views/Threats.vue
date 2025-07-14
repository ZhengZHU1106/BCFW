<template>
  <div class="threats-page">
    <div class="page-header">
      <h2>Threat Detection</h2>
      <button @click="simulateAttack" class="btn btn-danger" :disabled="isSimulating">
        {{ isSimulating ? 'Simulating...' : '🚨 Simulate Attack' }}
      </button>
    </div>

    <!-- Latest Threat Alert -->
    <div class="latest-threat" v-if="latestThreat">
      <ThreatAlert :threat="latestThreat" />
    </div>

    <!-- Threat Statistics -->
    <div class="threat-stats">
      <div class="stats-grid">
        <div class="stat-card card">
          <div class="stat-icon danger">🔥</div>
          <div class="stat-info">
            <div class="stat-value">{{ threatStats.high }}</div>
            <div class="stat-label">High Risk</div>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon warning">⚠️</div>
          <div class="stat-info">
            <div class="stat-value">{{ threatStats.medium }}</div>
            <div class="stat-label">Medium Risk</div>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon info">ℹ️</div>
          <div class="stat-info">
            <div class="stat-value">{{ threatStats.low }}</div>
            <div class="stat-label">Low Risk</div>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon success">✅</div>
          <div class="stat-info">
            <div class="stat-value">{{ threatStats.blocked }}</div>
            <div class="stat-label">Blocked</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Threat List -->
    <div class="threats-list card">
      <div class="card-header">
        <h3 class="card-title">Threat Detection Records</h3>
        <button @click="refreshThreats" class="btn btn-secondary btn-sm">
          Refresh
        </button>
      </div>
      
      <div v-if="threats.length === 0" class="no-threats">
        <p>No threat detection records</p>
      </div>
      
      <div v-else class="threats-table">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Threat Type</th>
              <th>Target IP</th>
              <th>Confidence</th>
              <th>Response Level</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="threat in threats" :key="threat.id">
              <td>{{ formatTime(threat.detected_at) }}</td>
              <td>
                <span class="threat-type">{{ threat.threat_type }}</span>
              </td>
              <td>
                <code class="ip-address">{{ threat.source_ip }}</code>
              </td>
              <td>
                <span class="confidence-badge" :class="getConfidenceClass(threat.confidence)">
                  {{ (threat.confidence * 100).toFixed(1) }}%
                </span>
              </td>
              <td>
                <span class="response-level badge" :class="getResponseClass(threat.response_level)">
                  {{ getResponseText(threat.response_level) }}
                </span>
              </td>
              <td>
                <span class="status-badge badge" :class="getStatusClass(threat.status)">
                  {{ getStatusText(threat.status) }}
                </span>
              </td>
              <td>
                <button 
                  v-if="canCreateProposal(threat)" 
                  @click="createProposal(threat)"
                  class="btn btn-primary btn-sm"
                  :disabled="threat.creating"
                >
                  {{ threat.creating ? 'Creating...' : 'Create Proposal' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { systemAPI } from '@/api/system'
import ThreatAlert from '@/components/ThreatAlert.vue'

// Threat data
const threats = ref([])
const latestThreat = ref(null)
const isSimulating = ref(false)

// Threat statistics
const threatStats = ref({
  high: 0,
  medium: 0,
  low: 0,
  blocked: 0
})

// Current user role
const currentRole = ref('operator')

// Timer
let refreshTimer = null

// Simulate attack
const simulateAttack = async () => {
  if (isSimulating.value) return
  
  isSimulating.value = true
  try {
    const result = await systemAPI.simulateAttack()
    
    // Update latest threat
    latestThreat.value = {
      id: Date.now(),
      threat_type: result.threat_type,
      source_ip: result.source_ip || '192.168.1.100',
      confidence: result.confidence,
      response_level: result.response_level,
      status: result.auto_executed ? 'executed' : 'detected',
      detected_at: new Date().toISOString(),
      creating: false
    }
    
    // Refresh threat list
    await refreshThreats()
    
  } catch (error) {
    console.error('Attack simulation failed:', error)
    alert('Attack simulation failed. Please check backend service.')
  } finally {
    isSimulating.value = false
  }
}

// Refresh threat list
const refreshThreats = async () => {
  try {
    const result = await systemAPI.getDetectionLogs()
    if (result.success) {
      threats.value = result.data.map(threat => ({
        ...threat,
        creating: false
      }))
      
      // Update statistics
      updateThreatStats()
    }
  } catch (error) {
    console.error('Failed to refresh threat list:', error)
  }
}

// Update threat statistics
const updateThreatStats = () => {
  const stats = {
    high: 0,
    medium: 0,
    low: 0,
    blocked: 0
  }
  
  threats.value.forEach(threat => {
    if (threat.confidence > 0.8) {
      stats.high++
    } else if (threat.confidence > 0.5) {
      stats.medium++
    } else {
      stats.low++
    }
    
    if (threat.status === 'executed' || threat.status === 'approved') {
      stats.blocked++
    }
  })
  
  threatStats.value = stats
}

// Create proposal
const createProposal = async (threat) => {
  if (threat.creating) return
  
  threat.creating = true
  try {
    const result = await systemAPI.createProposal({
      detection_id: threat.id,
      action: 'block'
    })
    
    if (result.success) {
      alert('Proposal created successfully!')
      threat.status = 'proposal_created'
    }
  } catch (error) {
    console.error('Failed to create proposal:', error)
    alert('Failed to create proposal. Please try again later.')
  } finally {
    threat.creating = false
  }
}

// Check if proposal can be created
const canCreateProposal = (threat) => {
  return currentRole.value === 'operator' && 
         threat.response_level === 'manual' && 
         threat.status === 'detected'
}

// Get confidence level style
const getConfidenceClass = (confidence) => {
  if (confidence >= 0.8) return 'confidence-high'
  if (confidence >= 0.5) return 'confidence-medium'
  return 'confidence-low'
}

// Get response level style
const getResponseClass = (level) => {
  const mapping = {
    'auto': 'badge-success',
    'auto_proposal': 'badge-info',
    'manual': 'badge-warning',
    'silent': 'badge-secondary'
  }
  return mapping[level] || 'badge-secondary'
}

// Get response level text
const getResponseText = (level) => {
  const mapping = {
    'auto': 'Auto Response',
    'auto_proposal': 'Auto Proposal',
    'manual': 'Manual Decision',
    'silent': 'Silent Log'
  }
  return mapping[level] || 'Unknown'
}

// Get status style
const getStatusClass = (status) => {
  const mapping = {
    'detected': 'badge-warning',
    'executed': 'badge-success',
    'proposal_created': 'badge-info',
    'approved': 'badge-success'
  }
  return mapping[status] || 'badge-secondary'
}

// Get status text
const getStatusText = (status) => {
  const mapping = {
    'detected': 'Detected',
    'executed': 'Executed',
    'proposal_created': 'Proposal Created',
    'approved': 'Approved'
  }
  return mapping[status] || 'Unknown'
}

// Format time
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString('en-US')
}

// Listen for role changes
const handleRoleChange = (event) => {
  currentRole.value = event.detail.role
}

// Lifecycle
onMounted(() => {
  // Get current role
  currentRole.value = localStorage.getItem('userRole') || 'operator'
  
  // Listen for role changes
  window.addEventListener('roleChanged', handleRoleChange)
  
  // Initialize data
  refreshThreats()
  
  // Regular refresh
  refreshTimer = setInterval(refreshThreats, 10000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  window.removeEventListener('roleChanged', handleRoleChange)
})
</script>

<style scoped>
.threats-page {
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

.latest-threat {
  margin-bottom: 2rem;
}

.threat-stats {
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
  border-radius: 50%;
}

.stat-icon.danger {
  background-color: #fee;
}

.stat-icon.warning {
  background-color: #fff3cd;
}

.stat-icon.info {
  background-color: #d1ecf1;
}

.stat-icon.success {
  background-color: #d4edda;
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

.threats-list {
  overflow-x: auto;
}

.threats-table table {
  width: 100%;
  border-collapse: collapse;
}

.threats-table th,
.threats-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.threats-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #495057;
}

.threat-type {
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

.no-threats {
  text-align: center;
  padding: 3rem;
  color: #7f8c8d;
}

.no-threats p {
  margin: 0;
  font-size: 1.1rem;
}
</style>