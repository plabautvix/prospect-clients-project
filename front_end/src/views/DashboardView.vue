<script setup>
import { onMounted, computed } from 'vue'
import { useLeadsStore } from '@/stores/leads'
import { useOperationsStore } from '@/stores/operations'

const leadsStore = useLeadsStore()
const opsStore = useOperationsStore()

onMounted(() => {
  leadsStore.fetchStats()
  opsStore.fetchOperations()
})

const stats = computed(() => leadsStore.stats)
const total = computed(() => stats.value?.total ?? 0)
const activeOps = computed(() => opsStore.operations.filter((o) => o.status === 1))

// Duas entidades distintas, então duas matizes fixas. Os passos saíram do
// validador de paleta contra o fundo escuro: claros demais falhavam na faixa
// de luminosidade.
const SOURCE_STYLE = {
  maps: { label: 'Google Maps', color: '#0284c7' },
  instagram: { label: 'Instagram', color: '#db2777' },
}

function sourceStyle(id) {
  return SOURCE_STYLE[id] || { label: id, color: '#0284c7' }
}

function percent(value) {
  if (!total.value) return 0
  return Math.round((value / total.value) * 100)
}

// Barras de categoria medem grandeza, não identidade: uma matiz só, nunca uma
// cor por fatia.
const categories = computed(() => {
  const rows = stats.value?.por_categoria ?? []
  const maior = rows[0]?.total || 1
  return rows.map((row) => ({ ...row, width: Math.round((row.total / maior) * 100) }))
})

const sources = computed(() => {
  const rows = stats.value?.por_origem ?? []
  const maior = rows[0]?.total || 1
  return rows.map((row) => ({
    ...row,
    ...sourceStyle(row.origem),
    width: Math.round((row.total / maior) * 100),
    share: percent(row.total),
  }))
})

// O que falta para o lead ser abordável. Guardado como presente, não ausente,
// porque "82% com telefone" se lê melhor que "18% sem".
const completeness = computed(() => {
  if (!stats.value) return []
  return [
    { label: 'Com telefone', have: total.value - stats.value.sem_telefone },
    { label: 'Com site', have: total.value - stats.value.sem_site },
    { label: 'Com endereço', have: total.value - stats.value.sem_endereco },
  ].map((row) => ({ ...row, share: percent(row.have) }))
})

const kpis = computed(() => [
  { label: 'Total de leads', value: total.value, tone: 'text-txt-primary' },
  {
    label: 'Sem telefone nem site',
    value: stats.value?.sem_contato ?? 0,
    hint: 'Não há como abordar',
    tone: 'text-amber-400',
  },
  {
    label: 'Nichos distintos',
    value: stats.value?.total_categorias ?? 0,
    tone: 'text-txt-primary',
  },
  { label: 'Operações ativas', value: activeOps.value.length, tone: 'text-brand' },
])
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-extrabold text-txt-primary">Dashboard</h1>
      <p class="mt-1 text-sm text-txt-secondary">
        O que existe na sua base de leads hoje.
      </p>
    </div>

    <div v-if="!stats" class="card py-10 text-center text-sm text-txt-secondary/60">
      Carregando métricas…
    </div>

    <div v-else-if="total === 0" class="card py-10 text-center">
      <p class="text-sm text-txt-secondary/70">Nenhum lead coletado ainda.</p>
      <RouterLink to="/prospeccao" class="mt-3 inline-block text-sm text-brand hover:underline">
        Iniciar uma operação
      </RouterLink>
    </div>

    <template v-else>
      <!-- Números de cabeçalho: grandeza isolada não vira gráfico -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div v-for="kpi in kpis" :key="kpi.label" class="card">
          <p class="text-xs text-txt-secondary">{{ kpi.label }}</p>
          <p :class="['mt-1 text-3xl font-extrabold tabular-nums', kpi.tone]">
            {{ kpi.value }}
          </p>
          <p v-if="kpi.hint" class="mt-0.5 text-[11px] text-txt-secondary/50">
            {{ kpi.hint }}
          </p>
        </div>
      </div>

      <div class="grid gap-4 lg:grid-cols-2">
        <!-- Por fonte -->
        <div class="card">
          <h2 class="font-semibold text-txt-primary">Leads por fonte</h2>
          <p class="mt-0.5 text-xs text-txt-secondary/60">De onde vieram.</p>

          <div class="mt-5 space-y-4">
            <div v-for="s in sources" :key="s.origem">
              <div class="mb-1.5 flex items-baseline justify-between gap-3 text-sm">
                <span class="flex items-center gap-2 text-txt-secondary">
                  <span
                    class="h-2.5 w-2.5 shrink-0 rounded-sm"
                    :style="{ backgroundColor: s.color }"
                  ></span>
                  {{ s.label }}
                </span>
                <span class="tabular-nums text-txt-primary">
                  {{ s.total }}
                  <span class="ml-1 text-xs text-txt-secondary/50">{{ s.share }}%</span>
                </span>
              </div>
              <div class="h-2 w-full overflow-hidden rounded-full bg-white/5">
                <div
                  class="h-full rounded-full"
                  :style="{ width: `${s.width}%`, backgroundColor: s.color }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Completude -->
        <div class="card">
          <h2 class="font-semibold text-txt-primary">Completude do cadastro</h2>
          <p class="mt-0.5 text-xs text-txt-secondary/60">
            Quanto da base tem cada dado preenchido.
          </p>

          <div class="mt-5 space-y-4">
            <div v-for="c in completeness" :key="c.label">
              <div class="mb-1.5 flex items-baseline justify-between gap-3 text-sm">
                <span class="text-txt-secondary">{{ c.label }}</span>
                <span class="tabular-nums text-txt-primary">
                  {{ c.have }}
                  <span class="ml-1 text-xs text-txt-secondary/50">{{ c.share }}%</span>
                </span>
              </div>
              <div class="h-2 w-full overflow-hidden rounded-full bg-white/5">
                <div
                  class="h-full rounded-full bg-brand"
                  :style="{ width: `${c.share}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Nichos -->
      <div class="card">
        <div class="flex items-baseline justify-between gap-3">
          <h2 class="font-semibold text-txt-primary">Principais nichos</h2>
          <RouterLink to="/leads" class="text-xs text-brand hover:underline">
            Ver leads
          </RouterLink>
        </div>
        <p class="mt-0.5 text-xs text-txt-secondary/60">
          Os {{ categories.length }} maiores de {{ stats.total_categorias }} nichos.
        </p>

        <div class="mt-5 space-y-3">
          <div v-for="c in categories" :key="c.categoria" class="flex items-center gap-3">
            <span class="w-44 shrink-0 truncate text-sm text-txt-secondary" :title="c.categoria">
              {{ c.categoria }}
            </span>
            <div class="h-2.5 min-w-0 flex-1 overflow-hidden rounded-full bg-white/5">
              <div class="h-full rounded-full bg-brand" :style="{ width: `${c.width}%` }"></div>
            </div>
            <span class="w-12 shrink-0 text-right text-sm tabular-nums text-txt-primary">
              {{ c.total }}
            </span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
