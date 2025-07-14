import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Threats from '@/views/Threats.vue'
import Proposals from '@/views/Proposals.vue'
import History from '@/views/History.vue'

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
    }
  ]
})

export default router