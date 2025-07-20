import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Threats from '@/views/Threats.vue'
import Proposals from '@/views/Proposals.vue'
import History from '@/views/History.vue'
import Network from '@/views/Network.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/threats',
      name: 'threats',
      component: Threats
    },
    {
      path: '/proposals',
      name: 'proposals',
      component: Proposals
    },
    {
      path: '/history',
      name: 'history',
      component: History
    },
    {
      path: '/network',
      name: 'network',
      component: Network
    }
  ]
})

export default router