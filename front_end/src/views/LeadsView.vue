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
        <h1 class="text-2xl font-extrabold text-txt-primary">Leads</h1>
        <p class="mt-1 text-sm text-txt-secondary">{{ leadsStore.leads.length }} leads coletados.</p>
      </div>
      <button @click="leadsStore.fetchLeads()" class="btn-secondary">
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Atualizar
      </button>
    </div>

    <!-- Envio em lote -->
    <div v-if="selected.size > 0" class="card border-brand/20 bg-brand/5">
      <h2 class="mb-3 font-semibold text-txt-primary">
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
          <p class="mt-1.5 text-xs text-txt-secondary/60">Use <code class="rounded-md bg-surface-hover px-1.5 py-0.5 text-brand text-[11px]">{nome}</code> para personalizar com o nome do negócio.</p>
        </div>
        <div v-if="sendError" class="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-2.5 text-sm text-red-400">{{ sendError }}</div>
        <div v-if="sendResult" class="rounded-xl bg-brand/10 border border-brand/20 px-4 py-2.5 text-sm text-brand">
          {{ sendResult.sent }} enviadas / {{ sendResult.failed }} falhas de {{ sendResult.total }} total.
        </div>
        <div class="flex gap-2">
          <button @click="sendBatch" :disabled="sending" class="btn-primary">
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
      <svg class="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-txt-secondary/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input v-model="search" type="text" placeholder="Buscar por nome, telefone ou categoria…" class="input pl-10" />
    </div>

    <!-- Tabela -->
    <div class="card overflow-hidden p-0">
      <div v-if="leadsStore.loading" class="py-16 text-center text-sm text-txt-secondary/50">Carregando…</div>
      <div v-else-if="filtered.length === 0" class="py-16 text-center">
        <svg class="mx-auto h-10 w-10 text-txt-secondary/20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <p class="mt-2 text-sm text-txt-secondary/50">Nenhum lead encontrado.</p>
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="border-b border-brd-light bg-[#191c1a]">
            <tr>
              <th class="w-10 px-4 py-3">
                <input type="checkbox" :checked="allSelected" @change="toggleAll" class="rounded border-brd-light bg-surface text-brand focus:ring-brand/30" />
              </th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[#8a918c]">Nome</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[#8a918c]">Telefone</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[#8a918c] hidden md:table-cell">Categoria</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[#8a918c] hidden lg:table-cell">Endereço</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[#8a918c] hidden lg:table-cell">Site</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-brd-light">
            <tr
              v-for="lead in filtered"
              :key="lead.id_lead"
              :class="['transition-colors cursor-pointer', selected.has(lead.id_lead) ? 'bg-brand/5' : 'hover:bg-surface-hover']"
              @click="toggle(lead.id_lead)"
            >
              <td class="px-4 py-3" @click.stop>
                <input type="checkbox" :checked="selected.has(lead.id_lead)" @change="toggle(lead.id_lead)" class="rounded border-brd-light bg-surface text-brand focus:ring-brand/30" />
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2.5">
                  <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand/15 text-xs font-bold text-brand">
                    {{ lead.nome?.[0]?.toUpperCase() }}
                  </div>
                  <span class="font-medium text-txt-primary">{{ lead.nome }}</span>
                </div>
              </td>
              <td class="px-4 py-3 text-[#a1a8a4]">
                <span v-if="lead.telefone">{{ lead.telefone }}</span>
                <span v-else class="text-[#4a524d]">—</span>
              </td>
              <td class="px-4 py-3 hidden md:table-cell">
                <span v-if="lead.categoria" class="badge-blue">{{ lead.categoria }}</span>
                <span v-else class="text-[#4a524d]">—</span>
              </td>
              <td class="px-4 py-3 text-[#a1a8a4] hidden lg:table-cell max-w-[180px] truncate">
                {{ lead.endereco || '—' }}
              </td>
              <td class="px-4 py-3 hidden lg:table-cell">
                <a v-if="lead.site" :href="lead.site" target="_blank" class="text-brand hover:text-brand-hover transition-colors" @click.stop>
                  {{ lead.site.replace(/^https?:\/\//, '').substring(0, 30) }}
                </a>
                <span v-else class="text-[#4a524d]">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
