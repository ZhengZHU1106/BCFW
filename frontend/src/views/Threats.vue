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
        <div class="stat-card card">
          <div class="stat-icon normal">🛡️</div>
          <div class="stat-info">
            <div class="stat-value">{{ threatStats.benign }}</div>
            <div class="stat-label">Normal Traffic</div>
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
              <th>Type</th>
              <th>Target IP</th>
              <th>
                Confidence
                <button 
                  @click="showConfidenceExplanation = true"
                  class="confidence-info-btn"
                  title="Learn how confidence scores are calculated"
                >
                  ℹ️
                </button>
              </th>
              <th>Response Level</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="threat in threats" :key="threat.id" @click="showThreatDetails(threat)" class="threat-row">
              <td>{{ formatTime(threat.detected_at) }}</td>
              <td>
                <span class="threat-type">{{ threat.threat_type }}</span>
              </td>
              <td>
                <code class="ip-address">{{ threat.source_ip }}</code>
              </td>
              <td>
                <span class="confidence-badge" :class="getConfidenceClass(threat.confidence, threat.threat_type)">
                  {{ (threat.confidence * 100).toFixed(1) }}%
                </span>
              </td>
              <td>
                <span class="response-level badge" :class="getResponseClass(threat.response_level)">
                  {{ getResponseText(threat.response_level, threat.threat_type) }}
                </span>
              </td>
              <td>
                <span class="status-badge badge" :class="getStatusClass(threat.status)">
                  {{ getStatusText(threat.status) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Confidence Explanation Modal -->
    <ConfidenceExplanationModal 
      v-if="showConfidenceExplanation"
      @close="showConfidenceExplanation = false"
    />
    
    <!-- Threat Details Modal -->
    <ThreatDetailsModal 
      v-if="selectedThreat"
      :threat="selectedThreat"
      :current-role="currentRole"
      @close="selectedThreat = null"
      @create-proposal="handleCreateProposal"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { systemAPI } from '@/api/system'
import ThreatAlert from '@/components/ThreatAlert.vue'
import ConfidenceExplanationModal from '@/components/ConfidenceExplanationModal.vue'
import ThreatDetailsModal from '@/components/ThreatDetailsModal.vue'

// Threat data
const threats = ref([])
const latestThreat = ref(null)
const isSimulating = ref(false)

// Threat statistics
const threatStats = ref({
  high: 0,
  medium: 0,
  low: 0,
  blocked: 0,
  benign: 0
})

// Current user role
const currentRole = ref('operator')

// Modal control
const showConfidenceExplanation = ref(false)
const selectedThreat = ref(null)

// Timer
let refreshTimer = null

// Simulate attack
const simulateAttack = async () => {
  if (isSimulating.value) return
  
  isSimulating.value = true
  try {
    const result = await systemAPI.simulateAttack()
    
    // Extract data from nested structure
    const data = result.data || result
    
    // Update latest threat - 使用predicted_class保持与数据库一致
    latestThreat.value = {
      id: data.detection_id || Date.now(),
      threat_type: data.threat_info?.predicted_class || 'Unknown',
      true_label: data.threat_info?.true_label || 'Unknown',
      predicted_class: data.threat_info?.predicted_class || 'Unknown',
      source_ip: data.network_info?.source_ip || '192.168.1.100',
      confidence: data.threat_info?.confidence || 0,
      response_level: data.threat_info?.response_level || 'silent_logging',
      status: data.response_action?.action_taken === 'automatic_block' ? 'executed' : 'detected',
      detected_at: data.timestamp || new Date().toISOString(),
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
      // Show all detection records including normal traffic
      threats.value = result.data
        .map(threat => ({
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
    blocked: 0,
    benign: 0
  }
  
  threats.value.forEach(threat => {
    const threatType = threat.threat_type || threat.true_label
    
    if (threatType === 'Benign') {
      stats.benign++
    } else {
      // Only count confidence for actual threats
      if (threat.confidence > 0.8) {
        stats.high++
      } else if (threat.confidence > 0.5) {
        stats.medium++
      } else {
        stats.low++
      }
    }
    
    if (threat.status === 'executed' || threat.status === 'approved') {
      stats.blocked++
    }
  })
  
  threatStats.value = stats
}

// Show threat details modal
const showThreatDetails = (threat) => {
  selectedThreat.value = threat
}

// Handle create proposal from modal
const handleCreateProposal = async (threat) => {
  await createProposal(threat)
  selectedThreat.value = null // Close modal after creating proposal
}

// Create proposal
const createProposal = async (threat) => {
  if (threat.creating) return
  
  threat.creating = true
  try {
    // Get current operator role from localStorage
    const operatorRole = localStorage.getItem('userRole') || 'operator_0'
    
    const result = await systemAPI.createProposal({
      detection_id: threat.id,
      action: 'block',
      operator_role: operatorRole  // Pass operator role for Phase 8 role separation
    })
    
    if (result.success) {
      alert('Proposal created successfully!')
      threat.status = 'proposal_created'
      // Refresh proposals to show the new one
      await refreshThreats()
    }
  } catch (error) {
    console.error('Failed to create proposal:', error)
    alert('Failed to create proposal. Please try again later.')
  } finally {
    threat.creating = false
  }
}

// Note: canCreateProposal logic moved to ThreatDetailsModal component

// Get confidence level style
const getConfidenceClass = (confidence, threatType = null) => {
  // For Benign traffic, invert colors - high confidence is good (green)
  if (threatType === 'Benign') {
    if (confidence >= 0.8) return 'confidence-benign-high'  // Green - very safe
    if (confidence >= 0.5) return 'confidence-benign-medium' // Yellow - uncertain
    return 'confidence-benign-low'  // Red - suspicious
  }
  
  // For actual threats, high confidence is dangerous (red)
  if (confidence >= 0.8) return 'confidence-high'
  if (confidence >= 0.5) return 'confidence-medium'
  return 'confidence-low'
}

// Get response level style
const getResponseClass = (level) => {
  const mapping = {
    'automatic_response': 'badge-success',
    'auto_create_proposal': 'badge-info',
    'manual_decision_alert': 'badge-warning',
    'silent_logging': 'badge-secondary'
  }
  return mapping[level] || 'badge-secondary'
}

// Get response level text
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

// Get status style
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

// Get status text
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
  currentRole.value = localStorage.getItem('userRole') || 'operator_0'
  
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

.stat-icon.normal {
  background-color: #e3f2fd;
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

/* Benign-specific confidence colors (inverted logic) */
.confidence-benign-high {
  background-color: #d4edda;
  color: #27ae60;
}

.confidence-benign-medium {
  background-color: #fff3cd;
  color: #f39c12;
}

.confidence-benign-low {
  background-color: #fee;
  color: #e74c3c;
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

/* Confidence info button */
.confidence-info-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  margin-left: 0.5rem;
  padding: 0.2rem;
  border-radius: 3px;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.confidence-info-btn:hover {
  opacity: 1;
  background-color: #f8f9fa;
}

/* Clickable threat rows */
.threat-row {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.threat-row:hover {
  background-color: #f8f9fa;
}
</style>