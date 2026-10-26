<script setup>
defineProps({
  kind: { type: String, default: 'error' }, // error | success
})
</script>

<template>
  <div
    class="rounded-xl border px-4 py-2.5 text-sm"
    :class="kind === 'success'
      ? 'border-brand/20 bg-brand-soft text-brand'
      : 'border-red-500/20 bg-red-500/10 text-red-400'"
  >
    <slot />
  </div>
</template>
