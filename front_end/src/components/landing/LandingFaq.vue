<script setup>
import { ref } from 'vue'
import { useInView } from '@/composables/useInView'

const { el, visible } = useInView()
const open = ref(0)

const faqs = [
  {
    q: 'De onde vêm os leads?',
    a: 'Das fichas públicas de negócios no Google Maps, as mesmas informações que qualquer pessoa vê ao pesquisar. O Prospect apenas percorre os resultados da sua busca e organiza o que já está exposto ali.',
  },
  {
    q: 'Preciso deixar meu computador ligado?',
    a: 'Não. A coleta roda no servidor, em um navegador dedicado. Você inicia a operação, fecha a aba e volta depois para ver a lista.',
  },
  {
    q: 'Posso rodar mais de uma busca ao mesmo tempo?',
    a: 'Sim. Cada busca vira uma operação independente, com título e status próprios, e você pode parar qualquer uma delas no meio do caminho.',
  },
  {
    q: 'O Prospect entra em contato com os leads?',
    a: 'Não. Ele encontra e organiza os contatos; quem fala com o cliente é você, do jeito que preferir: telefone, e-mail ou visita. A ferramenta cuida da parte chata, que é achar quem ligar.',
  },
  {
    q: 'E a LGPD?',
    a: 'Os dados coletados são informações comerciais públicas, das fichas que os próprios negócios publicam. Ainda assim, quem faz o contato é você: vale identificar sua empresa logo no início e respeitar quem pedir para não ser procurado de novo.',
  },
  {
    q: 'Consigo filtrar a base depois?',
    a: 'Sim. A tela de leads filtra por nome, telefone, endereço, site e por várias categorias ao mesmo tempo, com paginação no servidor. Funciona igual com 200 ou 200 mil registros.',
  },
]
</script>

<template>
  <section id="faq" ref="el" :class="visible ? 'is-visible' : ''" class="section scroll-mt-28 py-24">
    <div class="grid gap-12 lg:grid-cols-[0.8fr_1.2fr]">
      <div>
        <span class="eyebrow reveal">Dúvidas</span>
        <h2 class="heading reveal mt-5" style="--d: 60ms">Perguntas que todo mundo faz antes de começar.</h2>
        <p class="reveal mt-4 text-sm text-txt-secondary" style="--d: 120ms">
          Ficou algo de fora? Escreva para
          <a href="mailto:contato@prospect.app" class="text-brand hover:text-brand-hover">contato@prospect.app</a>.
        </p>
      </div>

      <ul class="reveal space-y-3" style="--d: 160ms">
        <li
          v-for="(faq, i) in faqs"
          :key="faq.q"
          class="overflow-hidden rounded-2xl border border-brd-light bg-surface backdrop-blur-sm transition-colors"
          :class="open === i ? 'bg-surface-hover' : ''"
        >
          <button
            class="flex w-full items-center gap-4 px-5 py-4 text-left"
            :aria-expanded="open === i"
            @click="open = open === i ? -1 : i"
          >
            <span class="flex-1 text-sm font-medium text-txt-primary">{{ faq.q }}</span>
            <svg
              class="h-4 w-4 shrink-0 text-brand transition-transform duration-300"
              :class="open === i ? 'rotate-45' : ''"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-width="2" d="M12 5v14M5 12h14" />
            </svg>
          </button>
          <div v-show="open === i" class="px-5 pb-5 text-sm leading-relaxed text-txt-secondary">
            {{ faq.a }}
          </div>
        </li>
      </ul>
    </div>
  </section>
</template>
