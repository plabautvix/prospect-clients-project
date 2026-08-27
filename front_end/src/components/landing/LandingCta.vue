<script setup>
import { useInView } from '@/composables/useInView'

const { el, visible } = useInView()
</script>

<template>
  <section ref="el" :class="visible ? 'is-visible' : ''" class="section py-24">
    <div class="relative overflow-hidden rounded-2xl border border-brd-light bg-surface px-6 py-16 text-center backdrop-blur-sm sm:px-16">
      <div class="relative mx-auto max-w-2xl">
        <h2 class="reveal text-[clamp(2rem,5vw,3rem)] font-extrabold leading-tight tracking-tight">
          Enquanto você lê isso, alguém está<br class="hidden sm:block" />
          copiando telefone do Maps na mão.
        </h2>
        <p class="reveal mt-5 text-lg text-txt-secondary" style="--d: 80ms">
          Faça a primeira busca e veja a lista se montar sozinha.
        </p>
        <div class="reveal mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row" style="--d: 160ms">
          <RouterLink to="/login" class="btn-primary w-full px-7 py-3 text-base sm:w-auto">
            Entrar no Prospect
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5-5 5M6 12h12" />
            </svg>
          </RouterLink>
          <a href="#como-funciona" class="btn-secondary w-full px-7 py-3 text-base sm:w-auto">Rever como funciona</a>
        </div>
      </div>
    </div>
  </section>
</template>
