<template>
  <div class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>{{ node?.id?.replace('_', ' ')?.toUpperCase() || 'Node Details' }}</h3>
        <button @click="$emit('close')" class="close-btn">&times;</button>
      </div>
      
      <div class="modal-body">
        <!-- Basic Node Information -->
        <div class="info-section">
          <h4>Basic Information</h4>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">Node ID:</span>
              <span class="value">{{ node?.id || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">Role:</span>
              <span class="value badge" :class="`badge-${node?.type}`">
                {{ node?.role || '-' }}
              </span>
            </div>
            <div class="info-item">
              <span class="label">Address:</span>
              <span class="value address">{{ formatAddress(node?.address) }}</span>
            </div>
            <div class="info-item">
              <span class="label">Balance:</span>
              <span class="value balance">{{ formatBalance(node?.balance) }} ETH</span>
            </div>
            <div class="info-item">
              <span class="label">Status:</span>
              <span class="value status" :class="`status-${node?.status}`">
                {{ node?.status?.toUpperCase() || 'UNKNOWN' }}
              </span>
            </div>
            <div class="info-item">
              <span class="label">Nonce:</span>
              <span class="value">{{ nodeDetails?.node_info?.nonce || 0 }}</span>
            </div>
          </div>
        </div>

        <!-- Manager-specific Information -->
        <div v-if="node?.type === 'manager'" class="info-section">
          <h4>Manager Activity</h4>
          <div class="activity-stats">
            <div class="stat-card">
              <h5>{{ nodeDetails?.proposals_signed?.length || 0 }}</h5>
              <p>Proposals Signed</p>
            </div>
            <div class="stat-card">
              <h5>{{ getActiveProposals().length }}</h5>
              <p>Active Proposals</p>
            </div>
            <div class="stat-card">
              <h5>{{ getCompletedProposals().length }}</h5>
              <p>Completed</p>
            </div>
          </div>
          
          <!-- Recent Proposals -->
          <div v-if="nodeDetails?.proposals_signed?.length > 0" class="proposals-list">
            <h5>Recent Proposals</h5>
            <div class="proposal-item" v-for="proposal in nodeDetails.proposals_signed.slice(0, 5)" :key="proposal.id">
              <div class="proposal-header">
                <span class="proposal-id">#{{ proposal.id }}</span>
                <span class="proposal-status badge" :class="`badge-${proposal.status}`">
                  {{ proposal.status }}
                </span>
              </div>
              <div class="proposal-details">
                <p><strong>Threat:</strong> {{ proposal.threat_type }}</p>
                <p><strong>Date:</strong> {{ formatDate(proposal.created_at) }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Operator-specific Information -->
        <div v-if="node?.type === 'operator'" class="info-section">
          <h4>Operator Activity</h4>
          <div class="activity-stats">
            <div class="stat-card">
              <h5>{{ nodeDetails?.threat_detections?.length || 0 }}</h5>
              <p>Threats Detected</p>
            </div>
            <div class="stat-card">
              <h5>{{ getHighConfidenceDetections().length }}</h5>
              <p>High Confidence</p>
            </div>
            <div class="stat-card">
              <h5>{{ getRecentDetections().length }}</h5>
              <p>Recent (24h)</p>
            </div>
          </div>
          
          <!-- Recent Detections -->
          <div v-if="nodeDetails?.threat_detections?.length > 0" class="detections-list">
            <h5>Recent Threat Detections</h5>
            <div class="detection-item" v-for="detection in nodeDetails.threat_detections.slice(0, 5)" :key="detection.id">
              <div class="detection-header">
                <span class="detection-id">#{{ detection.id }}</span>
                <span class="confidence-badge" :class="getConfidenceClass(detection.confidence)">
                  {{ (detection.confidence * 100).toFixed(1) }}%
                </span>
              </div>
              <div class="detection-details">
                <p><strong>Type:</strong> {{ detection.threat_type }}</p>
                <p><strong>Time:</strong> {{ formatDate(detection.detected_at) }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Treasury-specific Information -->
        <div v-if="node?.type === 'treasury'" class="info-section">
          <h4>Treasury Activity</h4>
          <div class="activity-stats">
            <div class="stat-card">
              <h5>{{ getTotalRewards() }}</h5>
              <p>Total Rewards Sent</p>
            </div>
            <div class="stat-card">
              <h5>{{ getTotalTransactions() }}</h5>
              <p>Total Transactions</p>
            </div>
            <div class="stat-card">
              <h5>{{ getReserveRatio() }}%</h5>
              <p>Reserve Ratio</p>
            </div>
          </div>
          
          <div class="treasury-info">
            <p><strong>Primary Function:</strong> System reward distribution and funding</p>
            <p><strong>Connected Accounts:</strong> All Manager and Operator nodes</p>
            <p><strong>Auto-funding:</strong> Enabled for new accounts</p>
          </div>
        </div>

        <!-- Network Connections -->
        <div class="info-section">
          <h4>Network Connections</h4>
          <div class="connections-list">
            {{ getNodeConnections() }}
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <div class="footer-left">
          <button 
            v-if="canDeleteNode" 
            @click="handleDeleteClick" 
            class="btn btn-danger"
          >
            Delete Node
          </button>
        </div>
        <div class="footer-right">
          <button @click="$emit('refresh')" class="btn btn-secondary">
            Refresh Data
          </button>
          <button @click="$emit('close')" class="btn btn-primary">
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

// Props
const props = defineProps({
  node: {
    type: Object,
    default: () => ({})
  },
  nodeDetails: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits(['close', 'refresh', 'delete-node'])

// Handle overlay click to close modal
const handleOverlayClick = () => {
  emit('close')
}

// Format address for display
const formatAddress = (address) => {
  if (!address) return '-'
  return `${address.slice(0, 6)}...${address.slice(-4)}`
}

// Format balance
const formatBalance = (balance) => {
  if (balance === null || balance === undefined) return '0.0000'
  return parseFloat(balance).toFixed(4)
}

// Format date
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

// Get active proposals
const getActiveProposals = () => {
  return props.nodeDetails?.proposals_signed?.filter(p => p.status === 'pending') || []
}

// Get completed proposals
const getCompletedProposals = () => {
  return props.nodeDetails?.proposals_signed?.filter(p => p.status === 'executed') || []
}

// Get high confidence detections
const getHighConfidenceDetections = () => {
  return props.nodeDetails?.threat_detections?.filter(d => d.confidence > 0.8) || []
}

// Get recent detections (last 24h)
const getRecentDetections = () => {
  const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000)
  return props.nodeDetails?.threat_detections?.filter(d => {
    const detectionDate = new Date(d.detected_at)
    return detectionDate > oneDayAgo
  }) || []
}

// Get confidence class for styling
const getConfidenceClass = (confidence) => {
  if (confidence >= 0.9) return 'confidence-high'
  if (confidence >= 0.7) return 'confidence-medium'
  return 'confidence-low'
}

// Treasury-specific calculations
const getTotalRewards = () => {
  // This would typically come from transaction history
  return '12.34 ETH'
}

const getTotalTransactions = () => {
  return props.nodeDetails?.node_info?.nonce || 0
}

const getReserveRatio = () => {
  const balance = props.node?.balance || 0
  const totalSupply = 1000 // Assuming 1000 ETH total
  return ((balance / totalSupply) * 100).toFixed(1)
}

// Get node connections description
const getNodeConnections = () => {
  const nodeType = props.node?.type
  switch (nodeType) {
    case 'manager':
      return 'Connected to: Treasury, Other Managers (MultiSig), All Operators'
    case 'treasury':
      return 'Connected to: All Managers, All Operators (Funding)'
    case 'operator':
      return 'Connected to: All Managers (Proposals), Treasury (Funding)'
    default:
      return 'No active connections'
  }
}

// Check if node can be deleted (core nodes cannot be deleted)
const canDeleteNode = computed(() => {
  const coreNodes = ['treasury', 'manager_0', 'manager_1', 'manager_2']
  return props.node?.id && !coreNodes.includes(props.node.id)
})

// Handle delete click
const handleDeleteClick = () => {
  emit('delete-node', props.node)
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 1.5rem 0 1.5rem;
  border-bottom: 1px solid #e9ecef;
  margin-bottom: 1.5rem;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.25rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6c757d;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background-color: #f8f9fa;
  color: #495057;
}

.modal-body {
  padding: 0 1.5rem;
}

.info-section {
  margin-bottom: 2rem;
}

.info-section h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
  border-bottom: 2px solid #007bff;
  padding-bottom: 0.5rem;
}

.info-section h5 {
  margin: 0 0 0.75rem 0;
  color: #495057;
  font-size: 1rem;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-item .label {
  font-size: 0.875rem;
  color: #6c757d;
  font-weight: 500;
}

.info-item .value {
  font-size: 0.875rem;
  color: #2c3e50;
}

.address {
  font-family: monospace;
  background: #f8f9fa;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.balance {
  font-weight: 600;
  color: #28a745;
}

.status {
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.75rem;
}

.status-online {
  color: #28a745;
}

.status-offline {
  color: #dc3545;
}

.badge {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-align: center;
}

.badge-manager {
  background: #d1ecf1;
  color: #0c5460;
}

.badge-treasury {
  background: #d4edda;
  color: #155724;
}

.badge-operator {
  background: #ffeaa7;
  color: #856404;
}

.badge-pending {
  background: #fff3cd;
  color: #856404;
}

.badge-executed {
  background: #d4edda;
  color: #155724;
}

.activity-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
}

.stat-card h5 {
  margin: 0 0 0.25rem 0;
  font-size: 1.5rem;
  font-weight: bold;
  color: #007bff;
}

.stat-card p {
  margin: 0;
  font-size: 0.875rem;
  color: #6c757d;
}

.proposals-list,
.detections-list {
  margin-top: 1rem;
}

.proposal-item,
.detection-item {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 0.75rem;
  margin-bottom: 0.75rem;
}

.proposal-header,
.detection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.proposal-id,
.detection-id {
  font-weight: 600;
  color: #495057;
}

.confidence-badge {
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.confidence-high {
  background: #d4edda;
  color: #155724;
}

.confidence-medium {
  background: #fff3cd;
  color: #856404;
}

.confidence-low {
  background: #f8d7da;
  color: #721c24;
}

.proposal-details,
.detection-details {
  font-size: 0.875rem;
  color: #6c757d;
}

.proposal-details p,
.detection-details p {
  margin: 0.25rem 0;
}

.treasury-info {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  color: #495057;
}

.treasury-info p {
  margin: 0.5rem 0;
}

.connections-list {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  color: #495057;
}

.modal-footer {
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #e9ecef;
}

.footer-left {
  display: flex;
  gap: 0.75rem;
}

.footer-right {
  display: flex;
  gap: 0.75rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}

@media (max-width: 768px) {
  .modal-content {
    margin: 0.5rem;
    max-height: 95vh;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .activity-stats {
    grid-template-columns: 1fr;
  }
}
</style>