<template>
  <div class="modal-backdrop" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>Threat Detection Details</h3>
        <button @click="$emit('close')" class="close-btn">&times;</button>
      </div>
      
      <div class="modal-body">
        <!-- Basic Threat Information -->
        <div class="detail-section">
          <h4>Basic Information</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="label">Detection Time:</span>
              <span class="value">{{ formatTime(threat.detected_at) }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Threat Type:</span>
              <span class="value threat-type">{{ threat.true_label || threat.threat_type }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Source IP:</span>
              <code class="value">{{ threat.source_ip }}</code>
            </div>
            <div class="detail-item">
              <span class="label">Target IP:</span>
              <code class="value">{{ threat.target_ip || 'N/A' }}</code>
            </div>
            <div class="detail-item">
              <span class="label">Confidence:</span>
              <span class="value confidence" :class="getConfidenceClass(threat.confidence)">
                {{ (threat.confidence * 100).toFixed(1) }}%
              </span>
            </div>
            <div class="detail-item">
              <span class="label">Response Level:</span>
              <span class="value">{{ getResponseText(threat.response_level) }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Current Status:</span>
              <span class="value">{{ getStatusText(threat.status) }}</span>
            </div>
            <div class="detail-item" v-if="threat.proposal_id">
              <span class="label">Related Proposal:</span>
              <span class="value">#{{ threat.proposal_id }}</span>
            </div>
          </div>
        </div>

        <!-- AI Model Prediction Details -->
        <div class="detail-section" v-if="threat.detection_data">
          <h4>AI Model Analysis</h4>
          <div class="ai-analysis">
            <div class="prediction-info">
              <div class="prediction-item">
                <span class="label">Predicted Class:</span>
                <span class="value">{{ threat.detection_data.predicted_class }}</span>
              </div>
              <div class="prediction-item" v-if="threat.detection_data.hierarchical_info">
                <span class="label">Binary Classification:</span>
                <span class="value" :class="threat.detection_data.hierarchical_info.binary_prediction === 'Malicious' ? 'text-danger' : 'text-success'">
                  {{ threat.detection_data.hierarchical_info.binary_prediction }}
                  ({{ (threat.detection_data.hierarchical_info.binary_confidence * 100).toFixed(1) }}%)
                </span>
              </div>
            </div>
            
            <!-- Top Probabilities -->
            <div v-if="threat.detection_data.all_probabilities" class="probabilities">
              <h5>Class Probabilities</h5>
              <div class="probability-bars">
                <div 
                  v-for="(prob, index) in getTopProbabilities(threat.detection_data)" 
                  :key="index"
                  class="probability-item"
                >
                  <span class="class-name">{{ prob.class }}</span>
                  <div class="probability-bar">
                    <div 
                      class="probability-fill" 
                      :style="{ width: (prob.probability * 100) + '%' }"
                      :class="prob.probability > 0.5 ? 'high-prob' : 'low-prob'"
                    ></div>
                    <span class="probability-text">{{ (prob.probability * 100).toFixed(1) }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Taken -->
        <div class="detail-section" v-if="threat.action_taken">
          <h4>System Response</h4>
          <div class="response-info">
            <div class="response-item">
              <span class="label">Action Taken:</span>
              <span class="value">{{ threat.action_taken }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button @click="$emit('close')" class="btn btn-secondary">
          Close
        </button>
        <button @click="copyToClipboard" class="btn btn-info">
          Copy Details
        </button>
        <button 
          v-if="canCreateProposal(threat)" 
          @click="createProposal"
          class="btn btn-primary"
          :disabled="isCreating"
        >
          {{ isCreating ? 'Creating...' : 'Create Proposal' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  threat: {
    type: Object,
    required: true
  },
  currentRole: {
    type: String,
    default: 'operator_0'
  }
})

const emit = defineEmits(['close', 'create-proposal'])

// State
const isCreating = ref(false)

// Computed properties for probabilities
const getTopProbabilities = (detectionData) => {
  if (!detectionData.all_probabilities || !detectionData.class_names) {
    return []
  }
  
  const probabilities = detectionData.all_probabilities
    .map((prob, index) => ({
      class: detectionData.class_names[index],
      probability: prob
    }))
    .sort((a, b) => b.probability - a.probability)
    .filter(item => item.probability > 0.001) // Filter out very low probabilities
    .slice(0, 5) // Show top 5
  
  return probabilities
}

// Check if proposal can be created - Updated logic
const canCreateProposal = (threat) => {
  // Check if current role is an operator role
  const isOperator = props.currentRole.startsWith('operator')
  if (!isOperator) return false
  
  // Allow proposal creation for threats that haven't been automatically processed
  const allowedResponseLevels = ['manual_decision_alert', 'silent_logging']
  const allowedStatuses = ['detected', 'awaiting_decision']
  
  return allowedResponseLevels.includes(threat.response_level) && 
         allowedStatuses.includes(threat.status) &&
         !threat.proposal_id // Don't create if proposal already exists
}

// Create proposal
const createProposal = async () => {
  if (isCreating.value || !canCreateProposal(props.threat)) return
  
  isCreating.value = true
  try {
    await emit('create-proposal', props.threat)
  } catch (error) {
    console.error('Failed to create proposal:', error)
  } finally {
    isCreating.value = false
  }
}

// Copy to clipboard
const copyToClipboard = async () => {
  try {
    const content = JSON.stringify(props.threat, null, 2)
    await navigator.clipboard.writeText(content)
    alert('Threat details copied to clipboard')
  } catch (error) {
    console.error('Copy failed:', error)
    alert('Copy failed')
  }
}

// Style class methods
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

// Format time
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString('en-US')
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
  max-width: 900px;
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
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
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

.threat-type {
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

.text-danger {
  color: #dc3545;
}

.text-success {
  color: #28a745;
}

/* AI Analysis Styles */
.ai-analysis {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
}

.prediction-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.prediction-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.probabilities h5 {
  margin: 1rem 0 0.5rem 0;
  color: #495057;
  font-size: 1rem;
}

.probability-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.class-name {
  font-weight: 500;
  min-width: 100px;
  font-size: 0.875rem;
}

.probability-bar {
  flex: 1;
  height: 20px;
  background-color: #e9ecef;
  border-radius: 10px;
  position: relative;
  overflow: hidden;
}

.probability-fill {
  height: 100%;
  border-radius: 10px;
  transition: width 0.3s ease;
}

.probability-fill.high-prob {
  background: linear-gradient(90deg, #dc3545, #fd7e14);
}

.probability-fill.low-prob {
  background: linear-gradient(90deg, #28a745, #20c997);
}

.probability-text {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.75rem;
  font-weight: 600;
  color: #495057;
}

.response-info {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
}

.response-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #e0e0e0;
}

/* Responsive design */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    margin: 1rem;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
  }
  
  .probability-item {
    flex-direction: column;
    align-items: stretch;
    gap: 0.5rem;
  }
  
  .class-name {
    min-width: auto;
  }
}
</style>