<script setup>
defineProps({
  loading: { type: Boolean, default: false },
  label: { type: String, required: true },
  loadingLabel: { type: String, required: true },
})
</script>

<template>
  <button type="submit" :disabled="loading" class="btn-primary w-full">
    <svg v-if="loading" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
    </svg>
    {{ loading ? loadingLabel : label }}
  </button>
</template>
