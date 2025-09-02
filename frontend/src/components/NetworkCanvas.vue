<template>
  <div class="network-canvas-container">
    <canvas 
      ref="canvas"
      :width="canvasWidth"
      :height="canvasHeight"
      @click="handleCanvasClick"
      @mousemove="handleMouseMove"
      @mouseleave="handleMouseLeave"
    ></canvas>
    
    <!-- Node Legend -->
    <div class="node-legend">
      <h4>Node Types</h4>
      <div class="legend-item">
        <div class="legend-color" style="background: #007bff;"></div>
        <span>Manager</span>
      </div>
      <div class="legend-item">
        <div class="legend-color" style="background: #28a745;"></div>
        <span>Treasury</span>
      </div>
      <div class="legend-item">
        <div class="legend-color" style="background: #fd7e14;"></div>
        <span>Operator</span>
      </div>
    </div>

    <!-- Connection Lines Legend -->
    <div class="connection-legend">
      <h4>Network Status</h4>
      <div class="legend-item">
        <div class="connection-line" style="background: #28a745;"></div>
        <span>Active Connection</span>
      </div>
      <div class="legend-item">
        <div class="connection-line attack-flow" style="background: #dc3545;"></div>
        <span>Attack Flow</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'

// Props
const props = defineProps({
  nodes: {
    type: Array,
    default: () => []
  },
  layout: {
    type: String,
    default: 'star'
  },
  attackFlow: {
    type: Array,
    default: () => []
  },
  votingData: {
    type: Map,
    default: () => new Map()
  }
})

// Emits
const emit = defineEmits(['node-click', 'layout-updated'])

// Canvas refs and dimensions
const canvas = ref(null)
const canvasWidth = ref(800)
const canvasHeight = ref(600)

// Internal state
const ctx = ref(null)
const nodePositions = ref(new Map())
const hoveredNode = ref(null)
const animationFrame = ref(null)
const attackAnimations = ref([])

// Constants
const NODE_RADIUS = 20
const CONNECTION_WIDTH = 2
const ATTACK_ANIMATION_DURATION = 2000

// Initialize canvas
const initCanvas = () => {
  if (!canvas.value) return
  
  ctx.value = canvas.value.getContext('2d')
  updateCanvasSize()
  
  // Setup high DPI support
  const dpr = window.devicePixelRatio || 1
  const rect = canvas.value.getBoundingClientRect()
  
  canvas.value.width = rect.width * dpr
  canvas.value.height = rect.height * dpr
  
  ctx.value.scale(dpr, dpr)
  canvas.value.style.width = rect.width + 'px'
  canvas.value.style.height = rect.height + 'px'
  
  canvasWidth.value = rect.width
  canvasHeight.value = rect.height
}

// Update canvas size
const updateCanvasSize = () => {
  if (!canvas.value) return
  
  const container = canvas.value.parentElement
  canvasWidth.value = container.clientWidth
  canvasHeight.value = container.clientHeight
}

// Calculate node positions based on layout
const calculateNodePositions = (layout) => {
  const positions = new Map()
  const nodes = props.nodes
  const centerX = canvasWidth.value / 2
  const centerY = canvasHeight.value / 2
  const margin = 80
  
  if (nodes.length === 0) return positions

  switch (layout) {
    case 'star':
      // Treasury at center, managers in inner circle, operators in outer circle
      const treasuryNode = nodes.find(n => n.type === 'treasury')
      const managerNodes = nodes.filter(n => n.type === 'manager')
      const operatorNodes = nodes.filter(n => n.type === 'operator')
      
      if (treasuryNode) {
        positions.set(treasuryNode.id, { x: centerX, y: centerY })
      }
      
      // Position managers in inner circle
      managerNodes.forEach((node, index) => {
        const angle = (index * 2 * Math.PI) / managerNodes.length
        const radius = 120
        positions.set(node.id, {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle)
        })
      })
      
      // Position operators in outer circle
      operatorNodes.forEach((node, index) => {
        const angle = (index * 2 * Math.PI) / operatorNodes.length
        const radius = 220
        const position = {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle)
        }
        positions.set(node.id, position)
      })
      break

    case 'grid':
      // Organize nodes by type for better grid layout
      const gridTreasuryNodes = nodes.filter(n => n.type === 'treasury')
      const gridManagerNodes = nodes.filter(n => n.type === 'manager')
      const gridOperatorNodes = nodes.filter(n => n.type === 'operator')
      
      const cols = 4 // Fixed 4 columns for better organization
      const cellWidth = (canvasWidth.value - 2 * margin) / cols
      const cellHeight = (canvasHeight.value - 2 * margin) / 4 // 4 rows max
      
      // Place treasury in center-top position
      if (gridTreasuryNodes.length > 0) {
        positions.set(gridTreasuryNodes[0].id, {
          x: margin + 1.5 * cellWidth + cellWidth / 2, // Column 1.5 (center)
          y: margin + cellHeight / 2 // Row 0
        })
      }
      
      // Place managers in row 1
      gridManagerNodes.forEach((node, index) => {
        positions.set(node.id, {
          x: margin + index * cellWidth + cellWidth / 2,
          y: margin + 1 * cellHeight + cellHeight / 2
        })
      })
      
      // Place operators in rows 2-3
      gridOperatorNodes.forEach((node, index) => {
        const row = Math.floor(index / cols) + 2 // Start from row 2
        const col = index % cols
        positions.set(node.id, {
          x: margin + col * cellWidth + cellWidth / 2,
          y: margin + row * cellHeight + cellHeight / 2
        })
      })
      break

    case 'circle':
      const radius = Math.min(canvasWidth.value, canvasHeight.value) / 3
      nodes.forEach((node, index) => {
        const angle = (index * 2 * Math.PI) / nodes.length
        positions.set(node.id, {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle)
        })
      })
      break

    case 'random':
      nodes.forEach((node) => {
        positions.set(node.id, {
          x: margin + Math.random() * (canvasWidth.value - 2 * margin),
          y: margin + Math.random() * (canvasHeight.value - 2 * margin)
        })
      })
      break
  }
  
  return positions
}

// Draw a node
const drawNode = (node, position) => {
  if (!ctx.value) return
  
  const { x, y } = position
  const radius = node.size || NODE_RADIUS
  const isHovered = hoveredNode.value === node.id
  
  // Draw node shadow
  ctx.value.shadowColor = 'rgba(0,0,0,0.2)'
  ctx.value.shadowBlur = 5
  ctx.value.shadowOffsetX = 2
  ctx.value.shadowOffsetY = 2
  
  // Draw node circle
  ctx.value.beginPath()
  ctx.value.arc(x, y, radius + (isHovered ? 5 : 0), 0, 2 * Math.PI)
  ctx.value.fillStyle = node.color
  ctx.value.fill()
  
  // Draw node border
  ctx.value.shadowColor = 'transparent'
  ctx.value.lineWidth = isHovered ? 3 : 2
  ctx.value.strokeStyle = isHovered ? '#333' : '#fff'
  ctx.value.stroke()
  
  // Draw status indicator
  if (node.status === 'online') {
    ctx.value.beginPath()
    ctx.value.arc(x + radius - 5, y - radius + 5, 4, 0, 2 * Math.PI)
    ctx.value.fillStyle = '#28a745'
    ctx.value.fill()
    ctx.value.strokeStyle = '#fff'
    ctx.value.lineWidth = 1
    ctx.value.stroke()
  }
  
  // Draw voting indicator for manager nodes
  if (node.type === 'manager' && props.votingData && props.votingData.size > 0) {
    const votingState = props.votingData.get(node.id)
    if (votingState) {
      const indicatorX = x - radius + 5
      const indicatorY = y - radius + 5
      
      ctx.value.beginPath()
      ctx.value.arc(indicatorX, indicatorY, 8, 0, 2 * Math.PI)
      
      if (votingState.status === 'signed') {
        ctx.value.fillStyle = '#28a745'  // Green for signed
      } else if (votingState.status === 'pending') {
        ctx.value.fillStyle = '#ffc107'  // Yellow for pending
      } else {
        ctx.value.fillStyle = '#6c757d'  // Gray for inactive
      }
      
      ctx.value.fill()
      ctx.value.strokeStyle = '#fff'
      ctx.value.lineWidth = 2
      ctx.value.stroke()
      
      // Add checkmark for signed status
      if (votingState.status === 'signed') {
        ctx.value.strokeStyle = '#fff'
        ctx.value.lineWidth = 2
        ctx.value.beginPath()
        ctx.value.moveTo(indicatorX - 3, indicatorY)
        ctx.value.lineTo(indicatorX - 1, indicatorY + 2)
        ctx.value.lineTo(indicatorX + 3, indicatorY - 2)
        ctx.value.stroke()
      }
    }
  }
  
  // Draw node label
  ctx.value.font = '12px Arial'
  ctx.value.fillStyle = '#333'
  ctx.value.textAlign = 'center'
  ctx.value.fillText(node.id.replace('_', ' '), x, y + radius + 20)
  
  // Draw balance
  ctx.value.font = '10px Arial'
  ctx.value.fillStyle = '#666'
  ctx.value.fillText(`${node.balance.toFixed(2)} ETH`, x, y + radius + 35)
}

// Draw connections between nodes
const drawConnections = () => {
  if (!ctx.value || props.nodes.length === 0) return
  
  const treasuryNode = props.nodes.find(n => n.type === 'treasury')
  const managerNodes = props.nodes.filter(n => n.type === 'manager')
  
  if (!treasuryNode) return
  
  const treasuryPos = nodePositions.value.get(treasuryNode.id)
  if (!treasuryPos) return
  
  ctx.value.strokeStyle = '#28a745'
  ctx.value.lineWidth = CONNECTION_WIDTH
  ctx.value.globalAlpha = 0.6
  
  // Connect treasury to all managers
  managerNodes.forEach(manager => {
    const managerPos = nodePositions.value.get(manager.id)
    if (managerPos) {
      ctx.value.beginPath()
      ctx.value.moveTo(treasuryPos.x, treasuryPos.y)
      ctx.value.lineTo(managerPos.x, managerPos.y)
      ctx.value.stroke()
    }
  })
  
  // Connect managers to each other (for multisig)
  for (let i = 0; i < managerNodes.length; i++) {
    for (let j = i + 1; j < managerNodes.length; j++) {
      const pos1 = nodePositions.value.get(managerNodes[i].id)
      const pos2 = nodePositions.value.get(managerNodes[j].id)
      if (pos1 && pos2) {
        ctx.value.beginPath()
        ctx.value.moveTo(pos1.x, pos1.y)
        ctx.value.lineTo(pos2.x, pos2.y)
        ctx.value.stroke()
      }
    }
  }
  
  ctx.value.globalAlpha = 1.0
}

// Draw attack flow animations
const drawAttackFlow = () => {
  if (!ctx.value) return
  
  attackAnimations.value.forEach((animation, index) => {
    const progress = (Date.now() - animation.startTime) / ATTACK_ANIMATION_DURATION
    
    if (progress >= 1) {
      attackAnimations.value.splice(index, 1)
      return
    }
    
    const startPos = nodePositions.value.get(animation.from)
    const endPos = nodePositions.value.get(animation.to)
    
    if (startPos && endPos) {
      const currentX = startPos.x + (endPos.x - startPos.x) * progress
      const currentY = startPos.y + (endPos.y - startPos.y) * progress
      
      // Draw attack line
      ctx.value.strokeStyle = '#dc3545'
      ctx.value.lineWidth = 4
      ctx.value.globalAlpha = 0.8
      ctx.value.beginPath()
      ctx.value.moveTo(startPos.x, startPos.y)
      ctx.value.lineTo(currentX, currentY)
      ctx.value.stroke()
      
      // Draw moving particle
      ctx.value.fillStyle = '#dc3545'
      ctx.value.beginPath()
      ctx.value.arc(currentX, currentY, 6, 0, 2 * Math.PI)
      ctx.value.fill()
      
      ctx.value.globalAlpha = 1.0
    }
  })
}

// Main render function
const render = () => {
  if (!ctx.value) return
  
  // Clear canvas
  ctx.value.clearRect(0, 0, canvasWidth.value, canvasHeight.value)
  
  // Draw background
  ctx.value.fillStyle = '#f8f9fa'
  ctx.value.fillRect(0, 0, canvasWidth.value, canvasHeight.value)
  
  // Draw connections
  drawConnections()
  
  // Draw attack flow
  drawAttackFlow()
  
  // Draw nodes
  props.nodes.forEach(node => {
    const position = nodePositions.value.get(node.id)
    if (position) {
      drawNode(node, position)
    }
  })
  
  // Continue animation if needed
  if (attackAnimations.value.length > 0) {
    animationFrame.value = requestAnimationFrame(render)
  }
}

// Handle canvas click
const handleCanvasClick = (event) => {
  const rect = canvas.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  // Check if click is on a node
  for (const node of props.nodes) {
    const position = nodePositions.value.get(node.id)
    if (position) {
      const distance = Math.sqrt((x - position.x) ** 2 + (y - position.y) ** 2)
      const radius = node.size || NODE_RADIUS
      
      if (distance <= radius) {
        emit('node-click', node)
        return
      }
    }
  }
}

// Handle mouse move for hover effects
const handleMouseMove = (event) => {
  const rect = canvas.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  let newHoveredNode = null
  
  // Check if mouse is over a node
  for (const node of props.nodes) {
    const position = nodePositions.value.get(node.id)
    if (position) {
      const distance = Math.sqrt((x - position.x) ** 2 + (y - position.y) ** 2)
      const radius = node.size || NODE_RADIUS
      
      if (distance <= radius) {
        newHoveredNode = node.id
        canvas.value.style.cursor = 'pointer'
        break
      }
    }
  }
  
  if (!newHoveredNode) {
    canvas.value.style.cursor = 'default'
  }
  
  if (hoveredNode.value !== newHoveredNode) {
    hoveredNode.value = newHoveredNode
    render()
  }
}

// Handle mouse leave
const handleMouseLeave = () => {
  hoveredNode.value = null
  canvas.value.style.cursor = 'default'
  render()
}

// Update layout
const updateLayout = (newLayout) => {
  console.log(`Updating layout to ${newLayout} with ${props.nodes.length} nodes`)
  
  // Clear existing positions and repopulate
  nodePositions.value.clear()
  const newPositions = calculateNodePositions(newLayout)
  for (const [nodeId, position] of newPositions) {
    nodePositions.value.set(nodeId, position)
  }
  
  render()
  emit('layout-updated', newLayout)
}

// Animate attack flow
const animateAttackFlow = (flowSteps) => {
  attackAnimations.value = []
  
  // Create animations based on flow steps
  flowSteps.forEach((step, index) => {
    if (step.node && step.step > 1) {
      const prevStep = flowSteps[index - 1]
      if (prevStep && prevStep.node) {
        attackAnimations.value.push({
          from: prevStep.node,
          to: step.node,
          startTime: Date.now() + index * 500
        })
      }
    }
  })
  
  if (attackAnimations.value.length > 0) {
    render()
  }
}

// Update voting states
const updateVotingStates = (votingData) => {
  // This will trigger a re-render with updated voting states
  render()
}

// Clear voting states
const clearVotingStates = () => {
  // This will trigger a re-render without voting states
  render()
}

// Watch for prop changes
watch(() => props.nodes, (newNodes, oldNodes) => {
  console.log(`NetworkCanvas: Received ${newNodes.length} nodes (was ${oldNodes?.length || 0}):`, newNodes.map(n => n.id))
  
  // Force a complete refresh of positions
  nodePositions.value.clear()
  
  // Recalculate all positions for all nodes
  const newPositions = calculateNodePositions(props.layout)
  
  // Update positions map by copying values instead of replacing reference
  for (const [nodeId, position] of newPositions) {
    nodePositions.value.set(nodeId, position)
  }
  
  // Force re-render with delay to ensure proper update
  nextTick(() => {
    console.log(`Rendering ${newNodes.length} nodes on canvas`)
    console.log('All node positions:', [...nodePositions.value.entries()])
    render()
  })
}, { deep: true })

watch(() => props.layout, (newLayout) => {
  updateLayout(newLayout)
})

// Lifecycle
onMounted(() => {
  initCanvas()
  
  // Initialize positions properly
  const initialPositions = calculateNodePositions(props.layout)
  for (const [nodeId, position] of initialPositions) {
    nodePositions.value.set(nodeId, position)
  }
  
  render()
  
  // Handle window resize
  window.addEventListener('resize', () => {
    updateCanvasSize()
    
    // Recalculate positions on resize
    nodePositions.value.clear()
    const resizedPositions = calculateNodePositions(props.layout)
    for (const [nodeId, position] of resizedPositions) {
      nodePositions.value.set(nodeId, position)
    }
    
    render()
  })
})

// Expose methods
defineExpose({
  updateLayout,
  animateAttackFlow,
  updateVotingStates,
  clearVotingStates
})
</script>

<style scoped>
.network-canvas-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 600px;
}

canvas {
  display: block;
  width: 100%;
  height: 100%;
  background: #f8f9fa;
}

.node-legend,
.connection-legend {
  position: absolute;
  top: 1rem;
  background: rgba(255, 255, 255, 0.95);
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  min-width: 120px;
}

.node-legend {
  left: 1rem;
}

.connection-legend {
  left: 1rem;
  top: 180px;
}

.node-legend h4,
.connection-legend h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  color: #2c3e50;
  font-weight: 600;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.75rem;
  color: #495057;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid #fff;
}

.connection-line {
  width: 20px;
  height: 2px;
  border-radius: 1px;
}

.attack-flow {
  position: relative;
  overflow: hidden;
}

.attack-flow::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.8), transparent);
  animation: shimmer 1s infinite;
}

@keyframes shimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}
</style>