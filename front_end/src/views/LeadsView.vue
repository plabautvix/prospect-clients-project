<script setup>
import { ref, computed, reactive, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLeadsStore } from '@/stores/leads'
import { useCampaignsStore } from '@/stores/campaigns'
import NewCampaignModal from '@/components/campaigns/NewCampaignModal.vue'

const leadsStore = useLeadsStore()
const campaignsStore = useCampaignsStore()
const router = useRouter()

const SOURCES = [
  { id: 'maps', label: 'Google Maps' },
  { id: 'instagram', label: 'Instagram' },
]

function sourceLabel(id) {
  return SOURCES.find((s) => s.id === id)?.label || 'Google Maps'
}

// Nenhuma fonte marcada significa todas, que é o estado inicial esperado.
function toggleOrigem(id) {
  const i = localFilters.origem.indexOf(id)
  if (i === -1) localFilters.origem.push(id)
  else localFilters.origem.splice(i, 1)
}

// Filtros locais (espelham os campos do servidor), aplicados com debounce
const localFilters = reactive({ nome: '', categoria: [], telefone: '', endereco: '', site: '', origem: [], contato: '' })

// O que as campanhas já fizeram com o lead.
const CONTACT_FILTERS = [
  { id: '', label: 'Todos' },
  { id: 'nao_contatado', label: 'Não contatados' },
  { id: 'na_fila', label: 'Na fila' },
  { id: 'enviado', label: 'Já enviados' },
]

const CONTACT_STATUS = {
  enviado: { label: 'enviada', class: 'bg-emerald-500/10 text-emerald-400' },
  na_fila: { label: 'na fila', class: 'bg-white/10 text-txt-secondary' },
  falhou: { label: 'falhou', class: 'bg-red-500/10 text-red-400' },
}

function contactText(c) {
  const channel = c.channel === 'whatsapp' ? 'WhatsApp' : 'Instagram'
  const when = c.sent_at
    ? ` ${new Date(c.sent_at).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}`
    : ''
  return `${channel}: ${CONTACT_STATUS[c.status].label}${when}`
}

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
      () =>
        leadsStore.setFilters({
          ...localFilters,
          categoria: [...localFilters.categoria],
          origem: [...localFilters.origem],
        }),
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

// Envio: pelos leads marcados ou, sem seleção, por tudo o que o filtro mostra.
// O canal sugerido segue a origem: perfis do Instagram por DM, o resto por WhatsApp.
const sendTarget = ref(null)

function openSendSelected() {
  const leads = [...selected.value.values()]
  sendTarget.value = {
    leadIds: leads.map((l) => l.id_lead),
    filters: {},
    count: leads.length,
    defaultChannel: leads.every((l) => l.origem === 'instagram') ? 'instagram' : 'whatsapp',
  }
}

function openSendFiltered() {
  const origem = leadsStore.filters.origem
  sendTarget.value = {
    leadIds: [],
    filters: { ...leadsStore.filters },
    count: leadsStore.total,
    defaultChannel: origem.length === 1 && origem[0] === 'instagram' ? 'instagram' : 'whatsapp',
  }
}

function onCampaignCreated() {
  sendTarget.value = null
  selected.value.clear()
  router.push('/campanhas')
}

// Opt-out: quem pediu para não receber mensagem fica fora de toda campanha.
const allSelectedDnc = computed(() =>
  [...selected.value.values()].every((l) => l.nao_contatar)
)
const dncBusy = ref(false)

async function toggleDoNotContact() {
  dncBusy.value = true
  try {
    await campaignsStore.setDoNotContact([...selected.value.keys()], !allSelectedDnc.value)
    selected.value.clear()
    await leadsStore.fetchLeads()
  } finally {
    dncBusy.value = false
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
      <div class="flex gap-2">
        <button
          @click="openSendFiltered"
          class="btn-secondary"
          :disabled="leadsStore.total === 0"
          title="Enviar mensagem para todos os leads do filtro atual"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
          Enviar para todos ({{ leadsStore.total }})
        </button>
        <button @click="leadsStore.fetchLeads()" class="btn-secondary">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Atualizar
        </button>
      </div>
    </div>

    <!-- Seleção -->
    <div v-if="selected.size > 0" class="card flex items-center gap-4 border-brand/20 bg-brand/5 py-3">
      <p class="text-sm font-medium text-txt-primary">{{ selected.size }} lead(s) selecionado(s)</p>
      <div class="ml-auto flex gap-2">
        <button @click="openSendSelected" class="btn-primary text-xs">Enviar mensagem</button>
        <button @click="toggleDoNotContact" :disabled="dncBusy" class="btn-secondary text-xs">
          {{ allSelectedDnc ? 'Permitir contato' : 'Não contatar' }}
        </button>
        <button @click="selected.clear()" class="btn-secondary text-xs">Cancelar seleção</button>
      </div>
    </div>

    <!-- Filtros -->
    <div class="card">
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <label class="label">Fonte</label>
          <div class="flex gap-2">
            <button
              v-for="s in SOURCES"
              :key="s.id"
              type="button"
              @click="toggleOrigem(s.id)"
              :class="[
                'flex-1 rounded-xl border px-3 py-2 text-sm font-medium transition',
                localFilters.origem.includes(s.id)
                  ? 'border-brand/40 bg-brand/10 text-brand'
                  : 'border-brd-light text-txt-secondary hover:bg-surface-hover',
              ]"
            >
              {{ s.label }}
            </button>
          </div>
          <p class="mt-1.5 text-xs text-txt-secondary/50">
            {{ localFilters.origem.length === 0 ? 'Mostrando todas as fontes' : 'Filtrando' }}
          </p>
        </div>
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
        <div class="sm:col-span-2 lg:col-span-3">
          <label class="label">Contato</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="f in CONTACT_FILTERS"
              :key="f.id"
              type="button"
              @click="localFilters.contato = f.id"
              :class="[
                'rounded-xl border px-3 py-2 text-sm font-medium transition',
                localFilters.contato === f.id
                  ? 'border-brand/40 bg-brand/10 text-brand'
                  : 'border-brd-light text-txt-secondary hover:bg-surface-hover',
              ]"
            >
              {{ f.label }}
            </button>
          </div>
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
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[#8a918c]">Contato</th>
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
                  <span
                    :class="[
                      'ml-2 rounded-md px-1.5 py-0.5 text-[10px] font-medium',
                      lead.origem === 'instagram'
                        ? 'bg-pink-500/10 text-pink-400'
                        : 'bg-sky-500/10 text-sky-400',
                    ]"
                  >
                    {{ sourceLabel(lead.origem) }}
                  </span>
                  <span
                    v-if="lead.nao_contatar"
                    class="rounded-md bg-red-500/10 px-1.5 py-0.5 text-[10px] font-medium text-red-400"
                  >
                    não contatar
                  </span>
                </div>
              </td>
              <td class="px-4 py-3 text-[#a1a8a4]">
                <span v-if="lead.telefone">{{ lead.telefone }}</span>
                <span v-else class="text-[#4a524d]">—</span>
              </td>
              <td class="px-4 py-3">
                <div v-if="lead.contatos?.length" class="flex flex-col gap-1">
                  <span
                    v-for="c in lead.contatos"
                    :key="c.channel"
                    :class="['w-fit whitespace-nowrap rounded-md px-1.5 py-0.5 text-[11px] font-medium', CONTACT_STATUS[c.status].class]"
                  >
                    {{ contactText(c) }}
                  </span>
                </div>
                <span v-else class="text-xs text-[#4a524d]">nenhum</span>
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

    <NewCampaignModal
      v-if="sendTarget"
      :lead-ids="sendTarget.leadIds"
      :filters="sendTarget.filters"
      :target-count="sendTarget.count"
      :default-channel="sendTarget.defaultChannel"
      @close="sendTarget = null"
      @created="onCampaignCreated"
    />
  </div>
</template>
