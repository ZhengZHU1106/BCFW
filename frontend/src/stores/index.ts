/**
 * Pinia Store 配置
 * 统一的状态管理配置
 */

import { createPinia } from 'pinia'

export const pinia = createPinia()

// 导出所有 stores
export { useSystemStore } from './systemStore'
export { useProposalStore } from './proposalStore'
export { useUserStore } from './userStore'
export { useThreatStore } from './threatStore'