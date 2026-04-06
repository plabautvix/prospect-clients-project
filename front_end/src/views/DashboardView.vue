<script setup>
import { onMounted, computed } from 'vue'
import { useLeadsStore } from '@/stores/leads'
import { useOperationsStore } from '@/stores/operations'
import { useWhatsappStore } from '@/stores/whatsapp'

const leadsStore = useLeadsStore()
const opsStore = useOperationsStore()
const waStore = useWhatsappStore()

onMounted(async () => {
  await Promise.all([
    leadsStore.fetchLeads(),
    opsStore.fetchOperations(),
    waStore.fetchStatus(),
    waStore.fetchSentSummary(),
  ])
})

const activeOps = computed(() => opsStore.operations.filter(o => o.status === 1))

const stats = computed(() => [
  {
    label: 'Total de Leads',
    value: leadsStore.leads.length,
    color: 'text-brand-600',
    bg: 'bg-brand-50',
    icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z',
  },
  {
    label: 'Operações Ativas',
    value: activeOps.value.length,
    color: 'text-amber-600',
    bg: 'bg-amber-50',
    icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
  },
  {
    label: 'Mensagens Enviadas',
    value: waStore.sentSummary.sent,
    color: 'text-emerald-600',
    bg: 'bg-emerald-50',
    icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
  },
  {
    label: 'Falhas de Envio',
    value: waStore.sentSummary.failed,
    color: 'text-red-600',
    bg: 'bg-red-50',
    icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
  },
])
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
      <p class="mt-1 text-sm text-gray-500">Visão geral das suas operações de prospecção.</p>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <div v-for="stat in stats" :key="stat.label" class="card flex items-center gap-4">
        <div :class="['flex h-11 w-11 shrink-0 items-center justify-center rounded-lg', stat.bg]">
          <svg :class="['h-5 w-5', stat.color]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" :d="stat.icon" />
          </svg>
        </div>
        <div>
          <p class="text-xs text-gray-500">{{ stat.label }}</p>
          <p :class="['text-2xl font-bold', stat.color]">{{ stat.value }}</p>
        </div>
      </div>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
      <!-- Operações ativas -->
      <div class="card">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="font-semibold text-gray-900">Operações ativas</h2>
          <RouterLink to="/prospeccao" class="text-xs text-brand-600 hover:underline">Ver todas</RouterLink>
        </div>
        <div v-if="activeOps.length === 0" class="py-8 text-center text-sm text-gray-400">
          Nenhuma operação em andamento.
        </div>
        <ul v-else class="divide-y divide-gray-100">
          <li v-for="op in activeOps" :key="op.id_operation" class="flex items-center justify-between py-2.5">
            <div>
              <p class="text-sm font-medium text-gray-900">{{ op.operation_name }}</p>
              <p class="text-xs text-gray-400">{{ op.search_text }}</p>
            </div>
            <span class="badge-green">Ativa</span>
          </li>
        </ul>
      </div>

      <!-- Últimos leads -->
      <div class="card">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="font-semibold text-gray-900">Últimos leads</h2>
          <RouterLink to="/leads" class="text-xs text-brand-600 hover:underline">Ver todos</RouterLink>
        </div>
        <div v-if="leadsStore.leads.length === 0" class="py-8 text-center text-sm text-gray-400">
          Nenhum lead encontrado ainda.
        </div>
        <ul v-else class="divide-y divide-gray-100">
          <li v-for="lead in leadsStore.leads.slice(0, 5)" :key="lead.id_lead" class="flex items-center gap-3 py-2.5">
            <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-700">
              {{ lead.nome?.[0]?.toUpperCase() }}
            </div>
            <div class="min-w-0">
              <p class="truncate text-sm font-medium text-gray-900">{{ lead.nome }}</p>
              <p class="truncate text-xs text-gray-400">{{ lead.telefone || 'Sem telefone' }}</p>
            </div>
          </li>
        </ul>
      </div>
    </div>

    <!-- WhatsApp status -->
    <div class="card flex items-center gap-4">
      <div :class="['flex h-10 w-10 shrink-0 items-center justify-center rounded-full', waStore.isReady ? 'bg-emerald-100' : 'bg-gray-100']">
        <svg :class="['h-5 w-5', waStore.isReady ? 'text-emerald-600' : 'text-gray-400']" fill="currentColor" viewBox="0 0 24 24">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
        </svg>
      </div>
      <div>
        <p class="text-sm font-medium text-gray-900">WhatsApp</p>
        <p class="text-xs text-gray-500">Status: <span :class="waStore.isReady ? 'text-emerald-600 font-medium' : 'text-gray-400'">{{ waStore.statusLabel }}</span></p>
      </div>
      <RouterLink v-if="!waStore.isReady" to="/whatsapp" class="ml-auto btn-secondary text-xs">
        Conectar
      </RouterLink>
    </div>
  </div>
</template>
