import { reactive, readonly } from 'vue'
import { systemAPI } from '@/api/system'

const state = reactive({
  overview: null,
  loading: false,
  error: null,
  cached: false,
  lastFetchedAt: null
})

const POLL_INTERVAL = 30000
let pollTimer = null
let subscribers = 0

async function fetchOverview(force = false) {
  if (state.loading) {
    return
  }

  state.loading = true
  if (force) {
    state.error = null
  }

  try {
    const response = await systemAPI.getSystemOverview()
    state.overview = response.data || null
    state.cached = Boolean(response.cached)
    state.lastFetchedAt = new Date().toISOString()
    state.error = null
  } catch (error) {
    console.error('Failed to fetch system overview:', error)
    state.error = error
  } finally {
    state.loading = false
  }
}

function startPolling() {
  if (pollTimer) {
    return
  }
  fetchOverview(true)
  pollTimer = setInterval(() => fetchOverview(), POLL_INTERVAL)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

export function useSystemOverviewStore() {
  const subscribe = () => {
    subscribers += 1
    if (subscribers === 1) {
      startPolling()
    } else if (!state.overview && !state.loading) {
      fetchOverview(true)
    }
  }

  const unsubscribe = () => {
    subscribers = Math.max(0, subscribers - 1)
    if (subscribers === 0) {
      stopPolling()
    }
  }

  return {
    state: readonly(state),
    fetchOverview: () => fetchOverview(true),
    subscribe,
    unsubscribe
  }
}
