<script setup>
defineProps({
  subtitle: { type: String, required: true },
})
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-dark-base px-4 py-12">
    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="mb-10 flex flex-col items-center gap-3">
        <RouterLink to="/" class="text-4xl font-extrabold tracking-tight">
          <span class="text-brand">Pr</span><span class="text-txt-primary">ospect</span>
        </RouterLink>
        <p class="text-center text-sm text-txt-secondary">{{ subtitle }}</p>
      </div>

      <slot />

      <div v-if="$slots.footer" class="mt-6 text-center text-sm text-txt-secondary">
        <slot name="footer" />
      </div>
    </div>
  </div>
</template>
