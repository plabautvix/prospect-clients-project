<script setup>
import { ref, computed, onMounted } from 'vue'
import { useLeadsStore } from '@/stores/leads'
import { useWhatsappStore } from '@/stores/whatsapp'

const leadsStore = useLeadsStore()
const waStore = useWhatsappStore()

const search = ref('')
const selected = ref(new Set())
const messageTemplate = ref('Olá {nome}! Vi seu negócio e gostaria de apresentar uma oportunidade especial.')
const sending = ref(false)
const sendResult = ref(null)
const sendError = ref('')

onMounted(() => leadsStore.fetchLeads())

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  if (!q) return leadsStore.leads
  return leadsStore.leads.filter(l =>
    l.nome?.toLowerCase().includes(q) ||
    l.telefone?.includes(q) ||
    l.categoria?.toLowerCase().includes(q)
  )
})

const allSelected = computed(
  () => filtered.value.length > 0 && filtered.value.every(l => selected.value.has(l.id_lead))
)

function toggleAll() {
  if (allSelected.value) {
    filtered.value.forEach(l => selected.value.delete(l.id_lead))
  } else {
    filtered.value.forEach(l => selected.value.add(l.id_lead))
  }
}

function toggle(id) {
  if (selected.value.has(id)) selected.value.delete(id)
  else selected.value.add(id)
}

const selectedLeads = computed(() =>
  leadsStore.leads.filter(l => selected.value.has(l.id_lead))
)

async function sendBatch() {
  if (selected.value.size === 0) return
  if (!messageTemplate.value.trim()) return
  if (!waStore.isReady) {
    sendError.value = 'WhatsApp não está conectado. Vá para a aba WhatsApp.'
    return
  }
  sending.value = true
  sendError.value = ''
  sendResult.value = null
  try {
    const leadsWithPhone = selectedLeads.value.filter(l => l.telefone)
    if (leadsWithPhone.length === 0) {
      sendError.value = 'Nenhum lead selecionado tem telefone cadastrado.'
      return
    }
    const result = await waStore.sendBatch(leadsWithPhone, messageTemplate.value)
    sendResult.value = result
    selected.value.clear()
  } catch (e) {
    sendError.value = e.response?.data?.error || 'Erro ao enviar mensagens.'
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-start justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Leads</h1>
        <p class="mt-1 text-sm text-gray-500">{{ leadsStore.leads.length }} leads coletados.</p>
      </div>
      <button @click="leadsStore.fetchLeads()" class="btn-secondary">
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Atualizar
      </button>
    </div>

    <!-- Envio em lote -->
    <div v-if="selected.size > 0" class="card border-brand-200 bg-brand-50">
      <h2 class="mb-3 font-semibold text-gray-900">
        Enviar mensagem para {{ selected.size }} lead(s)
      </h2>
      <div class="space-y-3">
        <div>
          <label class="label">Modelo de mensagem</label>
          <textarea
            v-model="messageTemplate"
            rows="2"
            class="input resize-none"
            placeholder="Use {nome} para personalizar"
          />
          <p class="mt-1 text-xs text-gray-400">Use <code class="rounded bg-white px-1">{nome}</code> para personalizar com o nome do negócio.</p>
        </div>
        <div v-if="sendError" class="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">{{ sendError }}</div>
        <div v-if="sendResult" class="rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-2 text-sm text-emerald-700">
          ✓ {{ sendResult.sent }} enviadas · {{ sendResult.failed }} falhas de {{ sendResult.total }} total.
        </div>
        <div class="flex gap-2">
          <button @click="sendBatch" :disabled="sending" class="btn-success">
            <svg v-if="sending" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            {{ sending ? 'Enviando…' : 'Enviar via WhatsApp' }}
          </button>
          <button @click="selected.clear()" class="btn-secondary">Cancelar</button>
        </div>
      </div>
    </div>

    <!-- Busca -->
    <div class="relative">
      <svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input v-model="search" type="text" placeholder="Buscar por nome, telefone ou categoria…" class="input pl-9" />
    </div>

    <!-- Tabela -->
    <div class="card overflow-hidden p-0">
      <div v-if="leadsStore.loading" class="py-16 text-center text-sm text-gray-400">Carregando…</div>
      <div v-else-if="filtered.length === 0" class="py-16 text-center">
        <svg class="mx-auto h-10 w-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <p class="mt-2 text-sm text-gray-400">Nenhum lead encontrado.</p>
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="border-b border-gray-100 bg-gray-50">
            <tr>
              <th class="w-10 px-4 py-3">
                <input type="checkbox" :checked="allSelected" @change="toggleAll" class="rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
              </th>
              <th class="px-4 py-3 text-left font-medium text-gray-500">Nome</th>
              <th class="px-4 py-3 text-left font-medium text-gray-500">Telefone</th>
              <th class="px-4 py-3 text-left font-medium text-gray-500 hidden md:table-cell">Categoria</th>
              <th class="px-4 py-3 text-left font-medium text-gray-500 hidden lg:table-cell">Endereço</th>
              <th class="px-4 py-3 text-left font-medium text-gray-500 hidden lg:table-cell">Site</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr
              v-for="lead in filtered"
              :key="lead.id_lead"
              :class="['hover:bg-gray-50 transition-colors', selected.has(lead.id_lead) ? 'bg-brand-50' : '']"
              @click="toggle(lead.id_lead)"
              class="cursor-pointer"
            >
              <td class="px-4 py-3" @click.stop>
                <input type="checkbox" :checked="selected.has(lead.id_lead)" @change="toggle(lead.id_lead)" class="rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-700">
                    {{ lead.nome?.[0]?.toUpperCase() }}
                  </div>
                  <span class="font-medium text-gray-900">{{ lead.nome }}</span>
                </div>
              </td>
              <td class="px-4 py-3 text-gray-600">
                <span v-if="lead.telefone">{{ lead.telefone }}</span>
                <span v-else class="text-gray-300">—</span>
              </td>
              <td class="px-4 py-3 hidden md:table-cell">
                <span v-if="lead.categoria" class="badge-blue">{{ lead.categoria }}</span>
                <span v-else class="text-gray-300">—</span>
              </td>
              <td class="px-4 py-3 text-gray-500 hidden lg:table-cell max-w-[180px] truncate">
                {{ lead.endereco || '—' }}
              </td>
              <td class="px-4 py-3 hidden lg:table-cell">
                <a v-if="lead.site" :href="lead.site" target="_blank" class="text-brand-600 hover:underline" @click.stop>
                  {{ lead.site.replace(/^https?:\/\//, '').substring(0, 30) }}
                </a>
                <span v-else class="text-gray-300">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
