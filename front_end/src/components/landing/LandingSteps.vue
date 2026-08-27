<script setup>
import { useInView } from '@/composables/useInView'

const { el, visible } = useInView()

const steps = [
  {
    n: '01',
    title: 'Descreva quem você procura',
    text: 'Uma linha basta: “barbearias em São Paulo”, “clínicas veterinárias em Belo Horizonte”. É a mesma busca que você faria no Maps, só que ela não para mais no seu cansaço.',
    icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
  },
  {
    n: '02',
    title: 'A operação roda sozinha',
    text: 'Um navegador dedicado percorre os resultados e grava cada negócio encontrado: nome, telefone, categoria, endereço e site. Você acompanha o progresso ao vivo e pode parar quando quiser.',
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
  },
  {
    n: '03',
    title: 'A lista fica pronta para consulta',
    text: 'Nome, telefone, categoria, endereço e site organizados em uma base que você filtra do jeito que precisar. Abra, escolha quem interessa e ligue.',
    icon: 'M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z',
  },
]
</script>

<template>
  <section id="como-funciona" ref="el" :class="visible ? 'is-visible' : ''" class="section scroll-mt-28 py-24">
    <div class="max-w-2xl">
      <h2 class="heading reveal">
        Três passos entre uma busca<br class="hidden sm:block" /> e uma lista para ligar.
      </h2>
    </div>

    <ol class="mt-14 grid gap-5 md:grid-cols-3">
      <li
        v-for="(step, i) in steps"
        :key="step.n"
        class="card reveal group relative transition-colors duration-300 hover:bg-surface-hover"
        :style="{ '--d': 120 + i * 90 + 'ms' }"
      >
        <div class="flex items-center justify-between">
          <div class="flex h-11 w-11 items-center justify-center rounded-xl bg-brand/10">
            <svg class="h-5 w-5 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" :d="step.icon" />
            </svg>
          </div>
          <span class="text-sm font-extrabold text-white/15 transition-colors duration-300 group-hover:text-brand/40">{{ step.n }}</span>
        </div>
        <h3 class="mt-5 text-lg font-semibold text-txt-primary">{{ step.title }}</h3>
        <p class="mt-2 text-sm leading-relaxed text-txt-secondary">{{ step.text }}</p>
      </li>
    </ol>
  </section>
</template>
