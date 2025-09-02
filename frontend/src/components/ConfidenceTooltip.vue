<template>
  <div class="tooltip-container">
    <div class="tooltip-content">
      <div class="tooltip-header">
        <h4>📊 Confidence Score</h4>
      </div>
      
      <div class="formula-section">
        <div class="formula">
          Confidence(x) = σ(W<sub>2</sub> · ReLU(W<sub>1</sub> · x + b<sub>1</sub>) + b<sub>2</sub>)
        </div>
        <div class="formula-note">
          Where x = 77-dimensional feature vector
        </div>
      </div>
      
      <div class="thresholds-quick">
        <div class="threshold-line high">&gt; 90%: Auto Response</div>
        <div class="threshold-line medium-high">80-90%: Auto Proposal</div>
        <div class="threshold-line medium">70-80%: Manual Decision</div>
        <div class="threshold-line low">&lt; 70%: Silent Logging</div>
      </div>
      
      <div class="tooltip-footer">
        <span class="click-hint">Click for detailed explanation</span>
      </div>
    </div>
    <div class="tooltip-arrow"></div>
  </div>
</template>

<script setup>
// No props or emits needed for this simple tooltip
</script>

<style scoped>
.tooltip-container {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 8px;
  z-index: 1000;
}

.tooltip-content {
  background: rgba(33, 37, 41, 0.95);
  color: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  width: 300px;
  font-size: 0.85rem;
  backdrop-filter: blur(8px);
}

.tooltip-header h4 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
  color: #ffc107;
}

.formula-section {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  padding: 0.75rem;
  margin-bottom: 0.75rem;
  border-left: 3px solid #007bff;
}

.formula {
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  color: #e3f2fd;
  margin-bottom: 0.25rem;
  text-align: center;
}

.formula-note {
  font-size: 0.75rem;
  color: #b0bec5;
  text-align: center;
  font-style: italic;
}

.thresholds-quick {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
}

.threshold-line {
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.1);
}

.threshold-line.high {
  border-left: 3px solid #dc3545;
  color: #f8d7da;
}

.threshold-line.medium-high {
  border-left: 3px solid #007bff;
  color: #cce5ff;
}

.threshold-line.medium {
  border-left: 3px solid #ffc107;
  color: #fff3cd;
}

.threshold-line.low {
  border-left: 3px solid #6c757d;
  color: #d1d3d4;
}

.tooltip-footer {
  text-align: center;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.click-hint {
  font-size: 0.75rem;
  color: #adb5bd;
  font-style: italic;
}

.tooltip-arrow {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-top: 8px solid rgba(33, 37, 41, 0.95);
}

/* Animation */
.tooltip-container {
  animation: tooltipFadeIn 0.2s ease-out;
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .tooltip-content {
    width: 280px;
    font-size: 0.8rem;
  }
  
  .formula {
    font-size: 0.85rem;
  }
}
</style>