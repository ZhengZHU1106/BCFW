<template>
  <div class="proposals-page">
    <div class="page-header">
      <h2>Proposal Management</h2>
      <div class="header-actions">
        <select v-model="statusFilter" class="filter-select">
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
        <button @click="refreshProposals" class="btn btn-secondary">
          Refresh
        </button>
      </div>
    </div>

    <!-- Proposal Statistics -->
    <div class="proposals-stats">
      <div class="stats-grid">
        <div class="stat-card card">
          <div class="stat-value">{{ proposalStats.total }}</div>
          <div class="stat-label">Total Proposals</div>
        </div>
        <div class="stat-card card">
          <div class="stat-value">{{ proposalStats.pending }}</div>
          <div class="stat-label">Pending</div>
        </div>
        <div class="stat-card card">
          <div class="stat-value">{{ proposalStats.approved }}</div>
          <div class="stat-label">Approved</div>
        </div>
        <div class="stat-card card">
          <div class="stat-value">{{ proposalStats.rejected }}</div>
          <div class="stat-label">Rejected</div>
        </div>
      </div>
    </div>

    <!-- Proposal List -->
    <div class="proposals-list">
      <div v-if="filteredProposals.length === 0" class="no-proposals">
        <p>No proposals</p>
      </div>
      
      <div v-else class="proposals-grid">
        <ProposalCard 
          v-for="proposal in filteredProposals" 
          :key="proposal.id"
          :proposal="proposal"
          :current-role="currentRole"
          @sign="handleSignProposal"
          @refresh="refreshProposals"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { systemAPI } from '@/api/system'
import ProposalCard from '@/components/ProposalCard.vue'

// Proposal data
const proposals = ref([])
const statusFilter = ref('all')
const currentRole = ref('operator_0')

// Timer
let refreshTimer = null

// Computed properties
const filteredProposals = computed(() => {
  if (statusFilter.value === 'all') {
    return proposals.value
  }
  return proposals.value.filter(p => p.status === statusFilter.value)
})

const proposalStats = computed(() => {
  const stats = {
    total: proposals.value.length,
    pending: 0,
    approved: 0,
    rejected: 0
  }
  
  proposals.value.forEach(proposal => {
    if (proposal.status === 'pending') stats.pending++
    else if (proposal.status === 'approved') stats.approved++
    else if (proposal.status === 'rejected') stats.rejected++
  })
  
  return stats
})

// Refresh proposal list
const refreshProposals = async () => {
  try {
    const result = await systemAPI.getProposals()
    if (result.success && result.data) {
      // Combine all proposals from different categories
      proposals.value = [
        ...(result.data.pending || []),
        ...(result.data.approved || []),
        ...(result.data.rejected || [])
      ]
    }
  } catch (error) {
    console.error('Failed to refresh proposal list:', error)
  }
}

// Handle proposal signing
const handleSignProposal = async (proposalId, managerIndex) => {
  try {
    // Convert managerIndex to manager_role format
    const managerRole = `manager_${managerIndex}`
    const result = await systemAPI.signProposal(proposalId, managerRole)
    if (result.success) {
      // Refresh list
      await refreshProposals()
      alert('Proposal signed successfully!')
    }
  } catch (error) {
    console.error('Signing failed:', error)
    alert('Signing failed. Please try again later.')
  }
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
  refreshProposals()
  
  // Regular refresh
  refreshTimer = setInterval(refreshProposals, 5000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  window.removeEventListener('roleChanged', handleRoleChange)
})
</script>

<style scoped>
.proposals-page {
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

.proposals-stats {
  margin-bottom: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card {
  text-align: center;
  padding: 1.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #2c3e50;
}

.stat-label {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin-top: 0.5rem;
}

.proposals-list {
  margin-top: 2rem;
}

.proposals-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

.no-proposals {
  text-align: center;
  padding: 4rem;
  color: #7f8c8d;
}

.no-proposals p {
  margin: 0;
  font-size: 1.2rem;
}
</style>