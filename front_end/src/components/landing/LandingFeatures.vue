<script setup>
import { useInView } from '@/composables/useInView'

const { el, visible } = useInView()

const features = [
  {
    title: 'Leads com o que importa',
    text: 'Nome, telefone, categoria, endereço e site capturados direto da ficha do negócio no Maps, sem digitação.',
    icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M15 7a3 3 0 11-6 0 3 3 0 016 0z',
  },
  {
    title: 'Filtros que aguentam volume',
    text: 'Busque por nome, telefone, endereço, site e combine várias categorias ao mesmo tempo. Tudo filtrado e paginado no servidor, então a lista não trava com dezenas de milhares de linhas.',
    icon: 'M3 4h18M6 12h12M10 20h4',
    wide: true,
  },
  {
    title: 'Telefone direto da ficha',
    text: 'O número que o negócio publicou no Maps vem junto com o resto. É abrir a lista e ligar.',
    icon: 'M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z',
  },
  {
    title: 'Várias operações ao mesmo tempo',
    text: 'Cada busca vira uma operação independente, com título, status ao vivo e botão de parar. Rode “dentistas SP” e “academias RJ” lado a lado.',
    icon: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z',
  },
  {
    title: 'Painel de acompanhamento',
    text: 'Total de leads, operações ativas e as últimas capturas em uma tela só, para saber onde está a prospecção sem abrir planilha.',
    icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
    wide: true,
  },
  {
    title: 'A base fica com você',
    text: 'Cada operação alimenta a mesma base. O que você levantou no mês passado continua lá, junto com o resto, na hora de procurar.',
    icon: 'M4 7v10c0 1.657 3.582 3 8 3s8-1.343 8-3V7M4 7c0 1.657 3.582 3 8 3s8-1.343 8-3M4 7c0-1.657 3.582-3 8-3s8 1.343 8 3m0 5c0 1.657-3.582 3-8 3s-8-1.343-8-3',
  },
]
</script>

<template>
  <section id="recursos" ref="el" :class="visible ? 'is-visible' : ''" class="relative scroll-mt-28 py-24">
    <div class="section">
      <div class="max-w-2xl">
        <h2 class="heading reveal">
          Feito para quem prospecta<br class="hidden sm:block" /> em escala, não em lote de dez.
        </h2>
        <p class="reveal mt-4 text-txt-secondary" style="--d: 60ms">
          Buscar, anotar e organizar acontece enquanto a aba fica fechada.
          Sobra a parte que importa: falar com o cliente.
        </p>
      </div>

      <div class="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <article
          v-for="(f, i) in features"
          :key="f.title"
          class="card reveal group transition-colors duration-300 hover:bg-surface-hover"
          :class="f.wide ? 'lg:col-span-2' : ''"
          :style="{ '--d': 100 + i * 70 + 'ms' }"
        >
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 transition-transform duration-300 group-hover:scale-110">
            <svg class="h-5 w-5 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" :d="f.icon" />
            </svg>
          </div>
          <h3 class="mt-5 font-semibold text-txt-primary">{{ f.title }}</h3>
          <p class="mt-2 text-sm leading-relaxed text-txt-secondary">{{ f.text }}</p>
        </article>
      </div>
    </div>
  </section>
</template>
