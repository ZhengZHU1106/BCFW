<template>
  <div id="app">
    <nav class="navbar">
      <div class="nav-container">
        <h1 class="nav-title">Blockchain Security Platform</h1>
        <div class="nav-links">
          <router-link to="/" class="nav-link">Dashboard</router-link>
          <router-link to="/threats" class="nav-link">Threats</router-link>
          <router-link to="/proposals" class="nav-link">Proposals</router-link>
          <router-link to="/network" class="nav-link">Network</router-link>
          <router-link to="/history" class="nav-link">History</router-link>
        </div>
        <RoleSwitch />
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import RoleSwitch from '@/components/RoleSwitch.vue'
</script>

<style>
#app {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.navbar {
  background-color: #2c3e50;
  color: white;
  padding: 1rem 0;
  box-shadow: 0 2px 4px rgba(0,0,0,.1);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-title {
  font-size: 1.5rem;
  margin: 0;
}

.nav-links {
  display: flex;
  gap: 2rem;
  flex: 1;
  justify-content: center;
}

.nav-link {
  color: white;
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.3s;
}

.nav-link:hover {
  opacity: 0.8;
}

.router-link-active {
  border-bottom: 2px solid #3498db;
}

.main-content {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1rem;
}
</style>