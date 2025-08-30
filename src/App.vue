<script setup>
</script>

<template>
  <div class="app-container">
    <main class="main-content">
      <router-view></router-view>
    </main>
  </div>
</template>

<style scoped>
.app-container {
  max-height: 100%;
  min-width: 100%;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding: 0;
}
</style>
