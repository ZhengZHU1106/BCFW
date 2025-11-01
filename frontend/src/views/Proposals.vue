<template>
  <div class="proposals-page">
    <!-- Demo Mode Banner -->
    <div v-if="isDemoMode" class="demo-banner">
      🎯 <strong>Demo Mode Active</strong> - All role actions are available for demonstration
    </div>
    
    <div class="page-header">
      <h2>Proposal Management</h2>
      <div class="header-actions">
        <select v-model="statusFilter" class="filter-select">
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="withdrawn">Withdrawn</option>
          <option value="invalid">Invalid</option>
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
        <div class="stat-card card">
          <div class="stat-value">{{ proposalStats.withdrawn }}</div>
          <div class="stat-label">Withdrawn</div>
        </div>
        <div class="stat-card card">
          <div class="stat-value">{{ proposalStats.invalid }}</div>
          <div class="stat-label">Invalid</div>
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
          :key="`proposal-${proposal.id}-${proposal.status}`"
          :proposal="proposal"
          :current-role="currentRole"
          :is-demo-mode="isDemoMode"
          @sign="handleSignProposal"
          @refresh="refreshProposals"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { systemAPI } from '@/api/system'
import { useSystemOverviewStore } from '@/stores/systemOverviewStore'
import ProposalCard from '@/components/ProposalCard.vue'

const systemOverviewStore = useSystemOverviewStore()
const { state, subscribe, unsubscribe, fetchOverview } = systemOverviewStore

const statusFilter = ref('all')
const currentRole = ref('operator_0')
const isDemoMode = ref(false)
const signingInProgress = ref(new Set())

const proposals = computed(() => state.overview?.proposals?.history || [])

const filteredProposals = computed(() => {
  if (statusFilter.value === 'all') {
    return proposals.value
  }
  return proposals.value.filter((p) => p.status === statusFilter.value)
})

const proposalStats = computed(() => {
  const summary = state.overview?.proposals?.summary
  if (summary) {
    return {
      total: summary.total ?? proposals.value.length,
      pending: summary.pending ?? 0,
      approved: summary.approved ?? 0,
      rejected: summary.rejected ?? 0,
      withdrawn: summary.withdrawn ?? 0,
      invalid: summary.invalid ?? 0
    }
  }

  const stats = {
    total: proposals.value.length,
    pending: 0,
    approved: 0,
    rejected: 0,
    withdrawn: 0,
    invalid: 0
  }

  proposals.value.forEach((proposal) => {
    if (proposal.status === 'pending') stats.pending += 1
    else if (proposal.status === 'approved') stats.approved += 1
    else if (proposal.status === 'rejected') stats.rejected += 1
    else if (proposal.status === 'withdrawn') stats.withdrawn += 1
    else if (proposal.status === 'invalid') stats.invalid += 1
  })

  return stats
})

const refreshProposals = async () => {
  await fetchOverview()
}

const handleSignProposal = async (proposalId, managerIndex) => {
  const signingKey = `${proposalId}-${managerIndex}`

  if (signingInProgress.value.has(signingKey)) {
    console.log('Signing already in progress for this proposal and manager')
    return
  }

  signingInProgress.value.add(signingKey)
  let refreshed = false

  try {
    const result = await systemAPI.signProposal(proposalId, managerIndex)
    if (result.success) {
      await fetchOverview()
      refreshed = true

      const updatedProposal = proposals.value.find((p) => p.id === proposalId)
      if (!updatedProposal || updatedProposal.status !== 'pending') {
        alert('✅ Proposal approved and executed successfully! Rewards have been distributed.')
      } else {
        alert('✅ Proposal signed successfully! Waiting for additional signatures...')
      }
    }
  } catch (error) {
    console.error('Signing failed:', error)
      if (error.response?.status === 400) {
        const errorMsg = error.response.data?.detail || error.message
        if (errorMsg?.includes('提案状态不允许签名')) {
          alert('This proposal has already been executed by another manager.')
        } else if (errorMsg?.includes('已经签名过')) {
          alert('You have already signed this proposal.')
        } else if (errorMsg?.includes('marked invalid')) {
          alert('This proposal no longer exists on-chain and has been marked invalid for reference.')
        } else {
          alert(`Signing failed: ${errorMsg}`)
        }
    } else {
      alert('Signing failed. Please try again later.')
    }
  } finally {
    signingInProgress.value.delete(signingKey)
    if (!refreshed) {
      await fetchOverview()
    }
  }
}

const handleRoleChange = (event) => {
  currentRole.value = event.detail.role
}

const handleDemoModeChange = (event) => {
  isDemoMode.value = event.detail.isDemoMode
}

onMounted(() => {
  currentRole.value = localStorage.getItem('userRole') || 'operator_0'
  isDemoMode.value = localStorage.getItem('demoMode') === 'true'

  window.addEventListener('roleChanged', handleRoleChange)
  window.addEventListener('demoModeChanged', handleDemoModeChange)

  subscribe()
  fetchOverview()
})

onUnmounted(() => {
  window.removeEventListener('roleChanged', handleRoleChange)
  window.removeEventListener('demoModeChanged', handleDemoModeChange)
  unsubscribe()
})
</script>


<style scoped>
.proposals-page {
  padding: 1rem 0;
}

.demo-banner {
  background: linear-gradient(135deg, #3498db, #2980b9);
  color: white;
  padding: 0.75rem 1.5rem;
  text-align: center;
  margin-bottom: 1rem;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(52, 152, 219, 0.3);
  animation: pulse-banner 2s infinite alternate;
}

@keyframes pulse-banner {
  from { opacity: 0.9; }
  to { opacity: 1; }
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
