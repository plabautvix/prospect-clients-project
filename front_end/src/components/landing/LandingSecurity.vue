<script setup>
import { useInView } from '@/composables/useInView'

const { el, visible } = useInView()

const pipeline = [
  { label: 'Você', sub: 'define a busca' },
  { label: 'API', sub: 'cria a operação' },
  { label: 'Coletor', sub: 'varre o Maps' },
  { label: 'Base', sub: 'leads salvos' },
]

const points = [
  {
    title: 'Cada serviço com a própria identidade',
    text: 'O robô de coleta nunca usa a sua credencial: ele tem chave própria, com permissão só para o que precisa, revogável sem mexer em ninguém.',
    icon: 'M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z',
  },
  {
    title: 'Tudo cifrado entre as peças',
    text: 'A comunicação interna entre os serviços trafega sobre TLS. Nenhum comando ou dado circula em texto aberto na rede.',
    icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z',
  },
  {
    title: 'Sessão que expira',
    text: 'Login com senha protegida por bcrypt e token com validade. Sessão esquecida aberta não vira porta destrancada.',
    icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
  },
]
</script>

<template>
  <section id="seguranca" ref="el" :class="visible ? 'is-visible' : ''" class="relative scroll-mt-28 overflow-hidden py-24">
    <div class="section relative">
      <div class="mx-auto max-w-2xl text-center">
        <span class="eyebrow reveal">Arquitetura e segurança</span>
        <h2 class="heading reveal mt-5" style="--d: 60ms">
          Automação que roda sozinha<br class="hidden sm:block" /> precisa ser confiável.
        </h2>
        <p class="reveal mt-4 text-txt-secondary" style="--d: 120ms">
          O Prospect é dividido em serviços independentes. Os leads são gravados em lotes
          durante a coleta: se algo cair no meio, o que já foi encontrado continua na base.
        </p>
      </div>

      <div class="reveal mt-14 flex flex-col items-stretch gap-3 md:flex-row md:items-center" style="--d: 160ms">
        <template v-for="(node, i) in pipeline" :key="node.label">
          <div class="flex-1 rounded-2xl border border-brd-light bg-surface px-5 py-4 text-center backdrop-blur-sm">
            <p class="font-semibold text-txt-primary">{{ node.label }}</p>
            <p class="mt-0.5 text-xs text-txt-secondary">{{ node.sub }}</p>
          </div>
          <svg v-if="i < pipeline.length - 1" class="mx-auto h-5 w-5 shrink-0 rotate-90 text-brand/60 md:rotate-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5-5 5M6 12h12" />
          </svg>
        </template>
      </div>

      <div class="mt-6 grid gap-5 md:grid-cols-3">
        <article
          v-for="(p, i) in points"
          :key="p.title"
          class="card reveal"
          :style="{ '--d': 200 + i * 80 + 'ms' }"
        >
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10">
            <svg class="h-5 w-5 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" :d="p.icon" />
            </svg>
          </div>
          <h3 class="mt-5 font-semibold text-txt-primary">{{ p.title }}</h3>
          <p class="mt-2 text-sm leading-relaxed text-txt-secondary">{{ p.text }}</p>
        </article>
      </div>

    </div>
  </section>
</template>
