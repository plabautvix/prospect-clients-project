<script setup>
import AppSidebar from './AppSidebar.vue'
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-dark-base">
    <AppSidebar />
    <div class="flex flex-1 flex-col overflow-hidden">
      <main class="flex-1 overflow-y-auto p-6 lg:p-8">
        <RouterView />
      </main>
    </div>
  </div>
</template>
