<template>
  <div class="network-page">
    <div class="network-header">
      <h2>Blockchain Network Visualization</h2>
      <div class="network-controls">
        <div class="layout-selector">
          <label for="layout-select">Layout:</label>
          <select id="layout-select" v-model="selectedLayout" @change="updateLayout">
            <option value="star">Star</option>
            <option value="grid">Grid</option>
            <option value="circle">Circle</option>
            <option value="random">Random</option>
          </select>
        </div>
        <button @click="simulateAttackFlow" class="btn btn-danger" :disabled="isSimulating">
          {{ isSimulating ? 'Simulating...' : 'Simulate Attack Flow' }}
        </button>
        <button @click="loadActiveProposals" class="btn btn-warning" :disabled="loadingProposals">
          {{ loadingProposals ? 'Loading...' : 'Show Active Voting' }}
        </button>
        <button @click="refreshNetwork" class="btn btn-secondary">
          Refresh Network
        </button>
        <button @click="showCreateNodeModal" class="btn btn-success">
          Add Node
        </button>
      </div>
    </div>

    <!-- Network Statistics -->
    <div class="network-stats">
      <div class="stat-card">
        <h3>{{ totalNodes }}</h3>
        <p>Total Nodes</p>
      </div>
      <div class="stat-card">
        <h3>{{ onlineNodes }}</h3>
        <p>Online Nodes</p>
      </div>
      <div class="stat-card">
        <h3>{{ managerNodes }}</h3>
        <p>Manager Nodes</p>
      </div>
      <div class="stat-card">
        <h3>{{ operatorNodes }}</h3>
        <p>Operator Nodes</p>
      </div>
    </div>

    <!-- Network Canvas -->
    <div class="network-container">
      <NetworkCanvas 
        ref="networkCanvas"
        :nodes="nodes" 
        :layout="selectedLayout"
        :attack-flow="attackFlowSteps"
        :voting-data="managerVotes"
        @node-click="showNodeDetails"
        @layout-updated="onLayoutUpdated"
      />
    </div>

    <!-- Node Detail Modal -->
    <NodeDetail
      v-if="showNodeModal"
      :node="selectedNode"
      :node-details="nodeDetails"
      @close="closeNodeDetails"
      @refresh="refreshNodeDetails"
      @delete-node="handleDeleteNode"
    />

    <!-- Create Node Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click="closeCreateNodeModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>Create New Node</h3>
          <button @click="closeCreateNodeModal" class="btn-close">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="createNode">
            <div class="form-group">
              <label for="node-type">Node Type:</label>
              <select id="node-type" v-model="newNode.type" required>
                <option value="">Select Type</option>
                <option value="manager">Manager</option>
                <option value="operator">Operator</option>
              </select>
            </div>
            <div class="form-group">
              <label for="node-name">Custom Name (optional):</label>
              <input 
                id="node-name" 
                type="text" 
                v-model="newNode.name" 
                placeholder="e.g., test, backup, etc."
                pattern="[a-zA-Z0-9_]+"
                title="Only letters, numbers, and underscores allowed"
              />
            </div>
            <div class="form-actions">
              <button type="button" @click="closeCreateNodeModal" class="btn btn-secondary">
                Cancel
              </button>
              <button type="submit" class="btn btn-success" :disabled="isCreatingNode">
                {{ isCreatingNode ? 'Creating...' : 'Create Node' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click="closeDeleteModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>Delete Node</h3>
          <button @click="closeDeleteModal" class="btn-close">&times;</button>
        </div>
        <div class="modal-body">
          <div class="delete-warning">
            <p><strong>⚠️ Warning:</strong> You are about to delete node <code>{{ nodeToDelete?.id }}</code>.</p>
            <p>This action will:</p>
            <ul>
              <li>Transfer remaining balance back to Treasury</li>
              <li>Remove the node from the active network</li>
              <li>This action cannot be undone</li>
            </ul>
            <p v-if="nodeToDelete && nodeToDelete.balance > 0">
              Current balance: <strong>{{ nodeToDelete.balance.toFixed(2) }} ETH</strong>
            </p>
          </div>
          <div class="form-actions">
            <button @click="closeDeleteModal" class="btn btn-secondary">
              Cancel
            </button>
            <button @click="confirmDeleteNode" class="btn btn-danger" :disabled="isDeletingNode">
              {{ isDeletingNode ? 'Deleting...' : 'Delete Node' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Attack Flow Panel -->
    <div v-if="attackFlowSteps.length > 0" class="attack-flow-panel">
      <h3>Attack Flow Progress</h3>
      <div class="flow-steps">
        <div 
          v-for="step in attackFlowSteps" 
          :key="step.step"
          class="flow-step"
          :class="`step-${step.action}`"
        >
          <div class="step-number">{{ step.step }}</div>
          <div class="step-content">
            <h4>{{ step.description }}</h4>
            <p v-if="step.confidence">Confidence: {{ (step.confidence * 100).toFixed(1) }}%</p>
            <p v-if="step.node">Node: {{ step.node }}</p>
            <p v-if="step.nodes">Nodes: {{ step.nodes.join(', ') }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Voting Progress Panel -->
    <div v-if="votingSteps.length > 0 || loadingProposals" class="voting-panel">
      <h3>Multi-Signature Voting</h3>
      <div class="voting-overview">
        <div class="voting-progress">
          <div class="progress-circle">
            <svg width="80" height="80">
              <circle cx="40" cy="40" r="35" fill="none" stroke="#e0e0e0" stroke-width="6"/>
              <circle 
                cx="40" cy="40" r="35" fill="none" 
                stroke="#28a745" stroke-width="6"
                stroke-dasharray="220"
                :stroke-dashoffset="220 - (220 * (Array.from(managerVotes.values()).filter(v => v.status === 'signed').length / 2))"
                transform="rotate(-90 40 40)"
              />
            </svg>
            <div class="progress-text">
              {{ Array.from(managerVotes.values()).filter(v => v.status === 'signed').length }}/2
            </div>
          </div>
          <div class="voting-status">
            <span v-if="votingSteps.some(s => s.action === 'proposal_ready')" class="status-approved">✅ Ready for Execution</span>
            <span v-else-if="votingSteps.some(s => s.action === 'real_proposal_status')" class="status-voting">🗳️ Active Proposal</span>
            <span v-else-if="votingSteps.some(s => s.action === 'no_active_proposals')" class="status-idle">💤 No Active Proposals</span>
            <span v-else-if="loadingProposals" class="status-loading">⏳ Loading...</span>
            <span v-else class="status-pending">⏳ Awaiting Signatures</span>
          </div>
        </div>
      </div>
      
      <div class="manager-votes">
        <h4>Manager Signatures</h4>
        <div class="votes-list">
          <div v-for="node in nodes.filter(n => n.type === 'manager')" :key="node.id" class="vote-item">
            <div class="manager-info">
              <span class="manager-name">{{ node.id }}</span>
              <span class="manager-address">{{ node.address ? node.address.slice(0, 8) + '...' : '' }}</span>
            </div>
            <div class="vote-status">
              <span v-if="managerVotes.get(node.id)?.status === 'signed'" class="status-signed">✅ Signed</span>
              <span v-else-if="managerVotes.get(node.id)?.status === 'pending'" class="status-pending">⏳ Pending</span>
              <span v-else class="status-inactive">⚪ Not Started</span>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="votingSteps.length > 0" class="voting-steps">
        <h4>Recent Activity</h4>
        <div class="steps-list">
          <div v-for="step in votingSteps" :key="`vote-${step.step}`" class="voting-step">
            <div class="step-indicator">{{ step.step }}</div>
            <div class="step-details">
              <p>{{ step.description }}</p>
              <span v-if="step.progress" class="step-progress">Progress: {{ step.progress.toFixed(0) }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { networkAPI } from '@/api/network'
import NetworkCanvas from '@/components/NetworkCanvas.vue'
import NodeDetail from '@/components/NodeDetail.vue'

// Reactive data
const nodes = ref([])
const selectedLayout = ref('star')
const selectedNode = ref(null)
const nodeDetails = ref(null)
const showNodeModal = ref(false)
const attackFlowSteps = ref([])
const isSimulating = ref(false)
const loadingProposals = ref(false)
const votingSteps = ref([])
const managerVotes = ref(new Map())
const isLoading = ref(false)
const activeProposals = ref([])

// Node management modal data
const showCreateModal = ref(false)
const showDeleteModal = ref(false)
const nodeToDelete = ref(null)
const isCreatingNode = ref(false)
const isDeletingNode = ref(false)
const newNode = ref({
  type: '',
  name: ''
})

// Network canvas reference
const networkCanvas = ref(null)

// Computed statistics
const totalNodes = computed(() => nodes.value.length)
const onlineNodes = computed(() => nodes.value.filter(node => node.status === 'online').length)
const managerNodes = computed(() => nodes.value.filter(node => node.type === 'manager').length)
const operatorNodes = computed(() => nodes.value.filter(node => node.type === 'operator').length)

// Load network topology
const loadNetworkTopology = async () => {
  try {
    isLoading.value = true
    const result = await networkAPI.getTopology()
    if (result.success) {
      // Force Vue reactivity update by creating a new array
      nodes.value = [...result.data.nodes]
      console.log(`Loaded ${result.data.nodes.length} nodes:`, result.data.nodes.map(n => n.id))
      
      // Force canvas update with a small delay to ensure DOM is updated
      await nextTick()
      setTimeout(() => {
        if (networkCanvas.value) {
          console.log('Forcing canvas layout update')
          networkCanvas.value.updateLayout(selectedLayout.value)
        }
      }, 50)
    } else {
      console.error('Failed to load network topology:', result.error)
    }
  } catch (error) {
    console.error('Error loading network topology:', error)
  } finally {
    isLoading.value = false
  }
}

// Show node details
const showNodeDetails = async (node) => {
  try {
    selectedNode.value = node
    
    // Load detailed information for the node
    const result = await networkAPI.getNodeDetails(node.id)
    if (result.success) {
      nodeDetails.value = result.data
      showNodeModal.value = true
    }
  } catch (error) {
    console.error('Error loading node details:', error)
  }
}

// Close node details modal
const closeNodeDetails = () => {
  showNodeModal.value = false
  selectedNode.value = null
  nodeDetails.value = null
}

// Refresh node details
const refreshNodeDetails = async () => {
  if (selectedNode.value) {
    await showNodeDetails(selectedNode.value)
  }
}

// Update layout
const updateLayout = () => {
  if (networkCanvas.value) {
    networkCanvas.value.updateLayout(selectedLayout.value)
  }
}

// Layout updated callback
const onLayoutUpdated = (layout) => {
  selectedLayout.value = layout
}

// Simulate attack flow
const simulateAttackFlow = async () => {
  if (isSimulating.value) return
  
  isSimulating.value = true
  attackFlowSteps.value = []
  
  try {
    const result = await networkAPI.simulateAttackFlow({
      attack_type: 'network_scan',
      confidence: 0.85
    })
    
    if (result.success) {
      attackFlowSteps.value = result.data.flow_steps
      
      // Animate the attack flow on the canvas
      if (networkCanvas.value) {
        networkCanvas.value.animateAttackFlow(attackFlowSteps.value)
      }
    }
  } catch (error) {
    console.error('Error simulating attack flow:', error)
  } finally {
    isSimulating.value = false
  }
}

// Load active proposals and display real voting status
const loadActiveProposals = async () => {
  if (loadingProposals.value) return
  
  loadingProposals.value = true
  managerVotes.value.clear()
  votingSteps.value = []
  activeProposals.value = []
  
  try {
    // Load active proposals from API
    const response = await fetch('/api/proposals')
    const result = await response.json()
    
    if (result.success) {
      const proposals = result.data || []
      activeProposals.value = proposals.filter(p => p.status === 'pending')
      
      if (activeProposals.value.length === 0) {
        votingSteps.value.push({
          step: 1,
          action: 'no_active_proposals',
          description: 'No active proposals requiring signatures',
          progress: 0
        })
        return
      }
      
      // Focus on the most recent active proposal
      const currentProposal = activeProposals.value[0]
      
      // Get manager nodes
      const managerNodes = nodes.value.filter(node => node.type === 'manager')
      
      // Initialize voting states based on actual proposal status
      managerNodes.forEach((node, index) => {
        const managerRole = `manager_${index}`
        const hasSigned = currentProposal.signatures && currentProposal.signatures.includes(managerRole)
        
        managerVotes.value.set(node.id, {
          status: hasSigned ? 'signed' : 'pending',
          timestamp: hasSigned ? new Date() : null,
          managerRole: managerRole
        })
      })
      
      // Calculate progress
      const signedCount = currentProposal.signatures ? currentProposal.signatures.length : 0
      const requiredSignatures = 2
      const progress = (signedCount / requiredSignatures) * 100
      
      // Add voting status
      votingSteps.value.push({
        step: 1,
        action: 'real_proposal_status',
        description: `Proposal #${currentProposal.id}: ${currentProposal.threat_type} threat`,
        proposalId: currentProposal.id,
        progress: progress
      })
      
      votingSteps.value.push({
        step: 2,
        action: 'signature_status',
        description: `Signatures: ${signedCount}/${requiredSignatures} collected`,
        progress: progress
      })
      
      if (progress >= 100) {
        votingSteps.value.push({
          step: 3,
          action: 'proposal_ready',
          description: 'Proposal ready for execution',
          progress: 100
        })
      }
      
      // Update canvas
      if (networkCanvas.value) {
        networkCanvas.value.updateVotingStates(managerVotes.value)
      }
      
    } else {
      throw new Error(result.message || 'Failed to load proposals')
    }
    
  } catch (error) {
    console.error('Error loading active proposals:', error)
    votingSteps.value.push({
      step: 1,
      action: 'error',
      description: 'Failed to load proposal data',
      progress: 0
    })
  } finally {
    loadingProposals.value = false
  }
}

// Refresh network
const refreshNetwork = async () => {
  await loadNetworkTopology()
  attackFlowSteps.value = []
  managerVotes.value.clear()
  votingSteps.value = []
}

// Node management methods
const showCreateNodeModal = () => {
  newNode.value = { type: '', name: '' }
  showCreateModal.value = true
}

const closeCreateNodeModal = () => {
  showCreateModal.value = false
  newNode.value = { type: '', name: '' }
}

const createNode = async () => {
  if (!newNode.value.type) {
    console.error('Please select a node type')
    return
  }

  isCreatingNode.value = true
  try {
    const result = await networkAPI.createNode({
      type: newNode.value.type,
      name: newNode.value.name
    })

    if (result.success) {
      console.log('Node created successfully:', result.data)
      closeCreateNodeModal()
      await loadNetworkTopology() // Refresh the network
      // Wait a bit for the UI to update
      await new Promise(resolve => setTimeout(resolve, 100))
      console.log(`✅ Node ${result.data.node_id} created successfully with ${result.data.balance} ETH`)
      // Show success message without blocking alert
      const message = `✅ Node ${result.data.node_id} created successfully with ${result.data.balance} ETH`
      console.log(message)
    } else {
      console.error('Failed to create node: ' + (result.error || 'Unknown error'))
    }
  } catch (error) {
    console.error('Error creating node:', error)
  } finally {
    isCreatingNode.value = false
  }
}

const handleDeleteNode = (node) => {
  // Check if it's a core node
  const coreNodes = ['treasury', 'manager_0', 'manager_1', 'manager_2']
  if (coreNodes.includes(node.id)) {
    console.warn('Core nodes cannot be deleted')
    return
  }

  nodeToDelete.value = node
  showDeleteModal.value = true
  showNodeModal.value = false // Close the details modal
}

const closeDeleteModal = () => {
  showDeleteModal.value = false
  nodeToDelete.value = null
}

const confirmDeleteNode = async () => {
  if (!nodeToDelete.value) return

  isDeletingNode.value = true
  try {
    const result = await networkAPI.removeNode(nodeToDelete.value.id)

    if (result.success) {
      console.log('Node deleted successfully:', result.data)
      const deletedNodeId = nodeToDelete.value.id
      closeDeleteModal()
      await loadNetworkTopology() // Refresh the network
      // Wait a bit for the UI to update
      await new Promise(resolve => setTimeout(resolve, 100))
      console.log(`✅ Node ${deletedNodeId} deleted successfully. Balance transferred to Treasury.`)
    } else {
      console.error('Failed to delete node: ' + (result.error || 'Unknown error'))
    }
  } catch (error) {
    console.error('Error deleting node:', error)
  } finally {
    isDeletingNode.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadNetworkTopology()
})
</script>

<style scoped>
.network-page {
  padding: 1rem;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.network-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e9ecef;
}

.network-header h2 {
  margin: 0;
  color: #2c3e50;
}

.network-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.layout-selector {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.layout-selector label {
  font-weight: 500;
  color: #495057;
}

.layout-selector select {
  padding: 0.375rem 0.75rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background-color: white;
  color: #495057;
}

.network-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}

.stat-card {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  text-align: center;
}

.stat-card h3 {
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  font-weight: bold;
  color: #007bff;
}

.stat-card p {
  margin: 0;
  color: #6c757d;
  font-size: 0.875rem;
}

.network-container {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow: hidden;
  position: relative;
}

.attack-flow-panel {
  position: fixed;
  top: 50%;
  right: 1rem;
  transform: translateY(-50%);
  width: 300px;
  max-height: 80vh;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  padding: 1rem;
  overflow-y: auto;
  z-index: 1000;
}

.attack-flow-panel h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.flow-steps {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.flow-step {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.step-threat_detected {
  background-color: #fff3cd;
  border-color: #ffeaa7;
}

.step-proposal_created {
  background-color: #d1ecf1;
  border-color: #b8daff;
}

.step-awaiting_signatures {
  background-color: #f8d7da;
  border-color: #f5c6cb;
}

.step-number {
  background: #007bff;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
  flex-shrink: 0;
}

.step-content h4 {
  margin: 0 0 0.25rem 0;
  font-size: 0.875rem;
  color: #2c3e50;
}

.step-content p {
  margin: 0;
  font-size: 0.75rem;
  color: #6c757d;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background-color: #c82333;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #5a6268;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background-color: #218838;
}

.btn-warning {
  background-color: #ffc107;
  color: #212529;
}

.btn-warning:hover:not(:disabled) {
  background-color: #e0a800;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Modal Styles */
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
  z-index: 2000;
}

.modal {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
}

.btn-close {
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
}

.btn-close:hover {
  color: #495057;
}

.modal-body {
  padding: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #495057;
}

.form-group select,
.form-group input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 1rem;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1.5rem;
}

.delete-warning {
  padding: 1rem;
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.delete-warning p {
  margin: 0 0 0.5rem 0;
  color: #856404;
}

.delete-warning ul {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
  color: #856404;
}

.delete-warning code {
  background: #f8f9fa;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: monospace;
}

@media (max-width: 768px) {
  .network-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .network-controls {
    justify-content: space-between;
  }

  .network-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .attack-flow-panel {
    position: relative;
    right: auto;
    top: auto;
    transform: none;
    width: 100%;
    margin-top: 1rem;
  }
  
  .voting-panel {
    position: relative;
    right: auto;
    top: auto;
    transform: none;
    width: 100%;
    margin-top: 1rem;
  }
}

/* Voting Panel Styles */
.voting-panel {
  position: fixed;
  top: 50%;
  left: 1rem;
  transform: translateY(-50%);
  width: 320px;
  max-height: 80vh;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  padding: 1rem;
  overflow-y: auto;
  z-index: 1000;
  border: 1px solid #e9ecef;
}

.voting-panel h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
  text-align: center;
}

.voting-overview {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.voting-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.progress-circle {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-circle svg {
  transform: rotate(-90deg);
}

.progress-circle circle:last-child {
  transition: stroke-dashoffset 0.8s ease;
}

.progress-text {
  position: absolute;
  font-size: 1.2rem;
  font-weight: bold;
  color: #28a745;
}

.voting-status {
  text-align: center;
  font-size: 0.9rem;
  font-weight: 600;
}

.status-approved {
  color: #28a745;
}

.status-voting {
  color: #007bff;
  animation: pulse 1.5s infinite;
}

.status-pending {
  color: #6c757d;
}

.manager-votes {
  margin-bottom: 1.5rem;
}

.manager-votes h4 {
  margin: 0 0 0.75rem 0;
  color: #2c3e50;
  font-size: 1rem;
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 0.5rem;
}

.votes-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.vote-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.manager-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.manager-name {
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.9rem;
}

.manager-address {
  font-family: monospace;
  font-size: 0.75rem;
  color: #6c757d;
}

.vote-status {
  display: flex;
  align-items: center;
}

.status-signed {
  color: #28a745;
  font-weight: 600;
  font-size: 0.85rem;
}

.status-pending {
  color: #ffc107;
  font-weight: 600;
  font-size: 0.85rem;
  animation: pulse 2s infinite;
}

.status-inactive {
  color: #6c757d;
  font-size: 0.85rem;
}

.voting-steps {
  border-top: 1px solid #e9ecef;
  padding-top: 1rem;
}

.voting-steps h4 {
  margin: 0 0 0.75rem 0;
  color: #2c3e50;
  font-size: 0.95rem;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.voting-step {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #007bff;
}

.step-indicator {
  background: #007bff;
  color: white;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: bold;
  flex-shrink: 0;
  margin-top: 0.1rem;
}

.step-details p {
  margin: 0 0 0.25rem 0;
  font-size: 0.85rem;
  color: #2c3e50;
  line-height: 1.3;
}

.step-progress {
  font-size: 0.75rem;
  color: #6c757d;
  font-weight: 500;
}
</style>