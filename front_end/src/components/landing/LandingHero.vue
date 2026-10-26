<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const QUERY = 'restaurantes em Campinas'

const SAMPLE = [
  { name: 'Cantina Bella Napoli', cat: 'Restaurante italiano', phone: '(19) 9••••-1042' },
  { name: 'Sushi Nakamura',       cat: 'Restaurante japonês',  phone: '(19) 9••••-7731' },
  { name: 'Boteco do Zé',         cat: 'Bar e petiscos',       phone: '(19) 9••••-3388' },
  { name: 'Green Bowl',           cat: 'Comida saudável',      phone: '(19) 9••••-2095' },
  { name: 'Churrascaria Pampa',   cat: 'Churrascaria',         phone: '(19) 9••••-8814' },
]

const typed = ref('')
const leads = ref([])
const running = ref(false)
let timers = []

const savedCount = computed(() => leads.value.filter((l) => l.saved).length)

function at(fn, ms) {
  timers.push(setTimeout(fn, ms))
}

function clearTimers() {
  timers.forEach(clearTimeout)
  timers = []
}

function run() {
  clearTimers()
  typed.value = ''
  leads.value = []
  running.value = true

  QUERY.split('').forEach((char, i) => at(() => { typed.value += char }, 55 * (i + 1)))

  const start = 55 * QUERY.length + 450
  SAMPLE.forEach((lead, i) => {
    at(() => {
      leads.value.push({ ...lead, saved: false })
      at(() => {
        const found = leads.value[i]
        if (found) found.saved = true
      }, 850)
      if (i === SAMPLE.length - 1) at(() => { running.value = false }, 1100)
    }, start + i * 650)
  })
}

onMounted(run)
onBeforeUnmount(clearTimers)
</script>

<template>
  <section class="relative overflow-hidden pb-16 pt-36 sm:pt-44">
    <div class="section relative">
      <div class="mx-auto max-w-3xl text-center">
        <h1 class="text-[clamp(2.75rem,8vw,5rem)] font-extrabold leading-[1.05] tracking-tight">
          Seu próximo cliente<br />
          <span class="text-brand">já está no mapa.</span>
        </h1>

        <div class="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <RouterLink to="/login" class="btn-primary w-full px-7 py-3 text-base sm:w-auto">
            Começar agora
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5-5 5M6 12h12" />
            </svg>
          </RouterLink>
        </div>

        <p class="mt-4 text-sm text-txt-secondary/70">
          Sem planilha, sem copiar e colar, sem ninguém garimpando telefone à mão.
        </p>
      </div>

      <!-- Demonstração ao vivo -->
      <div class="relative mx-auto mt-16 max-w-3xl">
        <div class="pointer-events-none absolute -inset-px rounded-2xl bg-gradient-to-b from-brand/30 to-transparent" aria-hidden="true"></div>
        <div class="relative overflow-hidden rounded-2xl border border-brd-light bg-[#191c1a]/90 backdrop-blur-sm">
          <!-- Barra do app -->
          <div class="flex items-center gap-2 border-b border-brd-light px-4 py-3">
            <span class="h-2.5 w-2.5 rounded-full bg-white/15"></span>
            <span class="h-2.5 w-2.5 rounded-full bg-white/15"></span>
            <span class="h-2.5 w-2.5 rounded-full bg-white/15"></span>
            <span class="ml-3 text-xs text-txt-secondary">Prospect · nova operação</span>
            <span class="ml-auto badge" :class="running ? 'badge-brand' : 'badge-gray'">
              {{ running ? 'coletando…' : 'concluída' }}
            </span>
          </div>

          <div class="p-5 sm:p-6">
            <!-- Busca -->
            <div class="flex items-center gap-3 rounded-pill border border-brd-light bg-surface px-4 py-2.5">
              <svg class="h-4 w-4 shrink-0 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <span class="truncate text-sm text-txt-primary">{{ typed }}</span>
              <span class="h-4 w-px animate-pulse bg-brand"></span>
            </div>

            <!-- Leads chegando -->
            <ul class="mt-4 space-y-2">
              <li
                v-for="lead in leads"
                :key="lead.name"
                class="lead-in flex items-center gap-3 rounded-xl border border-brd-light bg-surface px-4 py-3 text-left"
              >
                <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand/15 text-sm font-bold text-brand">
                  {{ lead.name[0] }}
                </div>
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-medium text-txt-primary">{{ lead.name }}</p>
                  <p class="truncate text-xs text-txt-secondary">{{ lead.cat }} · {{ lead.phone }}</p>
                </div>
                <span class="badge shrink-0" :class="lead.saved ? 'badge-green' : 'badge-yellow'">
                  {{ lead.saved ? 'salvo na base' : 'processando' }}
                </span>
              </li>
              <li v-if="!leads.length" class="rounded-xl border border-dashed border-brd-light px-4 py-6 text-center text-sm text-txt-secondary">
                Aguardando os primeiros resultados…
              </li>
            </ul>

            <div class="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-brd-light pt-4 text-sm text-txt-secondary">
              <span><strong class="text-txt-primary">{{ leads.length }}</strong> leads coletados</span>
              <span><strong class="text-brand">{{ savedCount }}</strong> com telefone para ligar</span>
              <button class="ml-auto text-xs text-brand transition-colors hover:text-brand-hover" @click="run">
                rodar de novo ↻
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.lead-in {
  animation: fadeUp 400ms ease-out both;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
</style>
