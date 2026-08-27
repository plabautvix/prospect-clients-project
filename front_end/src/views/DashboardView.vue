<script setup>
import { onMounted, computed } from 'vue'
import { useLeadsStore } from '@/stores/leads'
import { useOperationsStore } from '@/stores/operations'

const leadsStore = useLeadsStore()
const opsStore = useOperationsStore()

onMounted(async () => {
  await Promise.all([
    leadsStore.fetchLeads(),
    opsStore.fetchOperations(),
  ])
})

const activeOps = computed(() => opsStore.operations.filter(o => o.status === 1))

const stats = computed(() => [
  {
    label: 'Total de Leads',
    value: leadsStore.leads.length,
    accent: 'text-brand',
    bg: 'bg-brand/10',
    icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z',
  },
  {
    label: 'Operações Ativas',
    value: activeOps.value.length,
    accent: 'text-amber-400',
    bg: 'bg-amber-500/10',
    icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
  },
])
</script>

<template>
  <div class="space-y-8">
    <div>
      <h1 class="text-2xl font-extrabold text-txt-primary">Dashboard</h1>
      <p class="mt-1 text-sm text-txt-secondary">Visão geral das suas operações de prospecção.</p>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 gap-4">
      <div v-for="stat in stats" :key="stat.label" class="card flex items-center gap-4">
        <div :class="['flex h-11 w-11 shrink-0 items-center justify-center rounded-xl', stat.bg]">
          <svg :class="['h-5 w-5', stat.accent]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" :d="stat.icon" />
          </svg>
        </div>
        <div>
          <p class="text-xs text-txt-secondary">{{ stat.label }}</p>
          <p :class="['text-2xl font-extrabold', stat.accent]">{{ stat.value }}</p>
        </div>
      </div>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
      <!-- Operações ativas -->
      <div class="card">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="font-semibold text-txt-primary">Operações ativas</h2>
          <RouterLink to="/prospeccao" class="text-xs text-brand hover:text-brand-hover transition-colors">Ver todas</RouterLink>
        </div>
        <div v-if="activeOps.length === 0" class="py-8 text-center text-sm text-txt-secondary/60">
          Nenhuma operação em andamento.
        </div>
        <ul v-else class="divide-y divide-brd-light">
          <li v-for="op in activeOps" :key="op.id_operation" class="flex items-center justify-between py-3">
            <div>
              <p class="text-sm font-medium text-txt-primary">{{ op.operation_name }}</p>
              <p class="text-xs text-txt-secondary/60">{{ op.search_text }}</p>
            </div>
            <span class="badge-green">Ativa</span>
          </li>
        </ul>
      </div>

      <!-- Últimos leads -->
      <div class="card">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="font-semibold text-txt-primary">Últimos leads</h2>
          <RouterLink to="/leads" class="text-xs text-brand hover:text-brand-hover transition-colors">Ver todos</RouterLink>
        </div>
        <div v-if="leadsStore.leads.length === 0" class="py-8 text-center text-sm text-txt-secondary/60">
          Nenhum lead encontrado ainda.
        </div>
        <ul v-else class="divide-y divide-brd-light">
          <li v-for="lead in leadsStore.leads.slice(0, 5)" :key="lead.id_lead" class="flex items-center gap-3 py-3">
            <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand/15 text-xs font-bold text-brand">
              {{ lead.nome?.[0]?.toUpperCase() }}
            </div>
            <div class="min-w-0">
              <p class="truncate text-sm font-medium text-txt-primary">{{ lead.nome }}</p>
              <p class="truncate text-xs text-txt-secondary/60">{{ lead.telefone || 'Sem telefone' }}</p>
            </div>
          </li>
        </ul>
      </div>
    </div>

  </div>
</template>
