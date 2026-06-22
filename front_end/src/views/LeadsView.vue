<script setup>
import { ref, computed, reactive, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useLeadsStore } from '@/stores/leads'
import { useWhatsappStore } from '@/stores/whatsapp'

const leadsStore = useLeadsStore()
const waStore = useWhatsappStore()

// Filtros locais (espelham os campos do servidor), aplicados com debounce
const localFilters = reactive({ nome: '', categoria: [], telefone: '', endereco: '', site: '' })

// Multiselect de categoria — painel é teleportado para o body para escapar
// dos stacking contexts dos cards (backdrop-filter cria contexto próprio).
const categoryOpen = ref(false)
const categoryBox = ref(null)
const categoryPanel = ref(null)
const categorySearchInput = ref(null)
const categorySearch = ref('')
const panelStyle = ref({})

const filteredCategories = computed(() => {
  const q = categorySearch.value.trim().toLowerCase()
  if (!q) return leadsStore.categories
  return leadsStore.categories.filter((c) => c.toLowerCase().includes(q))
})

function toggleCategory(c) {
  const idx = localFilters.categoria.indexOf(c)
  if (idx === -1) localFilters.categoria.push(c)
  else localFilters.categoria.splice(idx, 1)
}

function updatePanelPosition() {
  if (!categoryBox.value) return
  const r = categoryBox.value.getBoundingClientRect()
  panelStyle.value = {
    position: 'fixed',
    top: `${r.bottom + 4}px`,
    left: `${r.left}px`,
    width: `${r.width}px`,
  }
}

function toggleCategoryDropdown() {
  categoryOpen.value = !categoryOpen.value
  if (categoryOpen.value) {
    categorySearch.value = ''
    nextTick(() => {
      updatePanelPosition()
      categorySearchInput.value?.focus()
    })
  }
}

function onCategoryReposition() {
  if (categoryOpen.value) updatePanelPosition()
}

function onClickOutside(e) {
  const inBox = categoryBox.value && categoryBox.value.contains(e.target)
  const inPanel = categoryPanel.value && categoryPanel.value.contains(e.target)
  if (!inBox && !inPanel) categoryOpen.value = false
}

// Seleção entre páginas: guarda o objeto do lead, não só o id, para que
// seleções sobrevivam à troca de página (a lista só tem a página atual).
const selected = ref(new Map())

const messageTemplate = ref('Olá {nome}! Vi seu negócio e gostaria de apresentar uma oportunidade especial.')
const sending = ref(false)
const sendResult = ref(null)
const sendError = ref('')

onMounted(() => {
  leadsStore.fetchLeads()
  leadsStore.fetchCategories()
  document.addEventListener('click', onClickOutside)
  window.addEventListener('scroll', onCategoryReposition, true)
  window.addEventListener('resize', onCategoryReposition)
})

// Debounce dos filtros
let debounceTimer = null
watch(
  localFilters,
  () => {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(
      () => leadsStore.setFilters({ ...localFilters, categoria: [...localFilters.categoria] }),
      300
    )
  },
  { deep: true }
)
onUnmounted(() => {
  clearTimeout(debounceTimer)
  document.removeEventListener('click', onClickOutside)
  window.removeEventListener('scroll', onCategoryReposition, true)
  window.removeEventListener('resize', onCategoryReposition)
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(leadsStore.total / leadsStore.pageSize))
)

const allSelected = computed(
  () =>
    leadsStore.leads.length > 0 &&
    leadsStore.leads.every((l) => selected.value.has(l.id_lead))
)

function toggleAll() {
  if (allSelected.value) {
    leadsStore.leads.forEach((l) => selected.value.delete(l.id_lead))
  } else {
    leadsStore.leads.forEach((l) => selected.value.set(l.id_lead, l))
  }
}

function toggle(lead) {
  if (selected.value.has(lead.id_lead)) selected.value.delete(lead.id_lead)
  else selected.value.set(lead.id_lead, lead)
}

const selectedLeads = computed(() => Array.from(selected.value.values()))

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
    const leadsWithPhone = selectedLeads.value.filter((l) => l.telefone)
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
        <p class="mt-1 text-sm text-txt-secondary">{{ leadsStore.total }} leads coletados.</p>
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
          <button @click="selected.clear()" class="btn-secondary">Cancelar seleção</button>
        </div>
      </div>
    </div>

    <!-- Filtros -->
    <div class="card">
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <label class="label">Nome</label>
          <input v-model="localFilters.nome" type="text" placeholder="Buscar por nome…" class="input" />
        </div>
        <div ref="categoryBox" class="relative">
          <label class="label">Categoria</label>
          <button
            type="button"
            class="input flex w-full items-center justify-between text-left"
            @click="toggleCategoryDropdown"
          >
            <span v-if="localFilters.categoria.length === 0" class="text-txt-secondary/50">
              Selecionar categorias…
            </span>
            <span v-else class="truncate text-txt-primary">
              {{ localFilters.categoria.length }} selecionada(s)
            </span>
            <svg class="h-4 w-4 shrink-0 text-txt-secondary/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Dropdown (teleportado para o body) -->
          <Teleport to="body">
            <div
              v-if="categoryOpen"
              ref="categoryPanel"
              :style="panelStyle"
              class="z-[100] flex max-h-72 flex-col rounded-xl border border-brd-light bg-surface shadow-lg"
            >
              <!-- Busca dentro do dropdown -->
              <div class="border-b border-brd-light p-2">
                <input
                  ref="categorySearchInput"
                  v-model="categorySearch"
                  type="text"
                  placeholder="Digite para filtrar…"
                  class="input py-1.5 text-sm"
                  @keydown.enter.prevent="filteredCategories.length && toggleCategory(filteredCategories[0])"
                />
              </div>

              <div class="overflow-auto py-1">
                <p v-if="leadsStore.categories.length === 0" class="px-3 py-2 text-xs text-txt-secondary/50">
                  Nenhuma categoria disponível.
                </p>
                <p v-else-if="filteredCategories.length === 0" class="px-3 py-2 text-xs text-txt-secondary/50">
                  Nenhuma categoria corresponde a “{{ categorySearch }}”.
                </p>
                <button
                  v-for="c in filteredCategories"
                  :key="c"
                  type="button"
                  @click="toggleCategory(c)"
                  :class="[
                    'flex w-full items-center justify-between px-3 py-2 text-left text-sm transition-colors',
                    localFilters.categoria.includes(c)
                      ? 'bg-brand/10 text-brand font-medium'
                      : 'text-txt-primary hover:bg-surface-hover',
                  ]"
                >
                  {{ c }}
                  <svg
                    v-if="localFilters.categoria.includes(c)"
                    class="h-4 w-4 shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                </button>
              </div>
            </div>
          </Teleport>

          <!-- Chips selecionadas -->
          <div v-if="localFilters.categoria.length > 0" class="mt-2 flex flex-wrap gap-1.5">
            <span
              v-for="c in localFilters.categoria"
              :key="c"
              class="inline-flex items-center gap-1 rounded-full bg-brand/15 px-2.5 py-0.5 text-xs text-brand"
            >
              {{ c }}
              <button type="button" class="hover:text-brand-hover" @click="toggleCategory(c)">✕</button>
            </span>
          </div>
        </div>
        <div>
          <label class="label">Telefone</label>
          <input v-model="localFilters.telefone" type="text" placeholder="Buscar por telefone…" class="input" />
        </div>
        <div>
          <label class="label">Endereço</label>
          <input v-model="localFilters.endereco" type="text" placeholder="Buscar por endereço…" class="input" />
        </div>
        <div>
          <label class="label">Site</label>
          <input v-model="localFilters.site" type="text" placeholder="Buscar por site…" class="input" />
        </div>
      </div>
    </div>

    <!-- Tabela -->
    <div class="card overflow-hidden p-0">
      <div v-if="leadsStore.loading" class="py-16 text-center text-sm text-txt-secondary/50">Carregando…</div>
      <div v-else-if="leadsStore.leads.length === 0" class="py-16 text-center">
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
              v-for="lead in leadsStore.leads"
              :key="lead.id_lead"
              :class="['transition-colors cursor-pointer', selected.has(lead.id_lead) ? 'bg-brand/5' : 'hover:bg-surface-hover']"
              @click="toggle(lead)"
            >
              <td class="px-4 py-3" @click.stop>
                <input type="checkbox" :checked="selected.has(lead.id_lead)" @change="toggle(lead)" class="rounded border-brd-light bg-surface text-brand focus:ring-brand/30" />
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

      <!-- Paginação -->
      <div
        v-if="!leadsStore.loading && leadsStore.total > 0"
        class="flex items-center justify-between border-t border-brd-light px-4 py-3"
      >
        <p class="text-xs text-txt-secondary/60">
          Página {{ leadsStore.page }} de {{ totalPages }} · {{ leadsStore.total }} leads
        </p>
        <div class="flex gap-2">
          <button
            class="btn-secondary text-xs"
            :disabled="leadsStore.page <= 1"
            @click="leadsStore.setPage(leadsStore.page - 1)"
          >
            Anterior
          </button>
          <button
            class="btn-secondary text-xs"
            :disabled="leadsStore.page >= totalPages"
            @click="leadsStore.setPage(leadsStore.page + 1)"
          >
            Próxima
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
