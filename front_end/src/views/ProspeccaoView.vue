<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useOperationsStore } from '@/stores/operations'

const store = useOperationsStore()

const SOURCES = [
  {
    id: 'maps',
    label: 'Google Maps',
    hint: 'Coleta nome, telefone, endereço e site dos negócios encontrados.',
  },
  {
    id: 'instagram',
    label: 'Instagram',
    hint: 'Busca perfis pelo índice do Google. Não acessa o Instagram.',
  },
]

// O tipo guia o rótulo, o exemplo e as sugestões do campo principal. É ali que
// a busca costuma sair errada: "veterinária" traz clínica e profissional
// misturadas, enquanto "médica veterinária" e "clínica veterinária" separam.
const ENTITY_TYPES = [
  {
    id: 'pessoa',
    label: 'Pessoa física',
    subjectLabel: 'Profissão',
    placeholder: 'Ex: médica veterinária',
    suggestions: [
      'médica veterinária',
      'psicóloga',
      'advogado',
      'nutricionista',
      'arquiteta',
      'dentista',
      'fisioterapeuta',
      'personal trainer',
    ],
  },
  {
    id: 'empresa',
    label: 'Empresa',
    subjectLabel: 'Ramo de atuação',
    placeholder: 'Ex: clínica veterinária',
    suggestions: [
      'clínica veterinária',
      'pet shop',
      'escritório de advocacia',
      'academia',
      'restaurante',
      'barbearia',
      'imobiliária',
      'loja de roupas',
    ],
  },
]

const UFS = [
  { sigla: 'AC', nome: 'Acre' }, { sigla: 'AL', nome: 'Alagoas' },
  { sigla: 'AP', nome: 'Amapá' }, { sigla: 'AM', nome: 'Amazonas' },
  { sigla: 'BA', nome: 'Bahia' }, { sigla: 'CE', nome: 'Ceará' },
  { sigla: 'DF', nome: 'Distrito Federal' }, { sigla: 'ES', nome: 'Espírito Santo' },
  { sigla: 'GO', nome: 'Goiás' }, { sigla: 'MA', nome: 'Maranhão' },
  { sigla: 'MT', nome: 'Mato Grosso' }, { sigla: 'MS', nome: 'Mato Grosso do Sul' },
  { sigla: 'MG', nome: 'Minas Gerais' }, { sigla: 'PA', nome: 'Pará' },
  { sigla: 'PB', nome: 'Paraíba' }, { sigla: 'PR', nome: 'Paraná' },
  { sigla: 'PE', nome: 'Pernambuco' }, { sigla: 'PI', nome: 'Piauí' },
  { sigla: 'RJ', nome: 'Rio de Janeiro' }, { sigla: 'RN', nome: 'Rio Grande do Norte' },
  { sigla: 'RS', nome: 'Rio Grande do Sul' }, { sigla: 'RO', nome: 'Rondônia' },
  { sigla: 'RR', nome: 'Roraima' }, { sigla: 'SC', nome: 'Santa Catarina' },
  { sigla: 'SP', nome: 'São Paulo' }, { sigla: 'SE', nome: 'Sergipe' },
  { sigla: 'TO', nome: 'Tocantins' },
]

const LIMIT_PRESETS = [50, 100, 250, 500]

const source = ref('maps')
const entityType = ref('pessoa')
const subject = ref('')
const limitRegion = ref(true)
const uf = ref('')
const city = ref('')
const limit = ref(100)
const title = ref('')
const formError = ref('')
const formSuccess = ref('')
const starting = ref(false)
const stopping = ref(null)

onMounted(() => store.fetchOperations())

const activeOps = computed(() => store.operations.filter(o => o.status === 1))
const inactiveOps = computed(() => store.operations.filter(o => o.status === 0))
const current = computed(() => SOURCES.find(s => s.id === source.value))
const currentType = computed(() => ENTITY_TYPES.find(t => t.id === entityType.value))

// Mostrado na tela antes de iniciar: o usuário vê exatamente o que será
// pesquisado, em vez de descobrir pelo resultado.
const query = computed(() => {
  const parts = []
  if (subject.value.trim()) parts.push(subject.value.trim())
  if (limitRegion.value) {
    const cidade = city.value.trim()
    if (cidade && uf.value) parts.push(`${cidade}, ${uf.value}`)
    else if (cidade) parts.push(cidade)
    else if (uf.value) parts.push(ufName(uf.value))
    else parts.push('Brasil')
  }
  return parts.join(' ')
})

function ufName(sigla) {
  return UFS.find(u => u.sigla === sigla)?.nome || sigla
}

function sourceLabel(id) {
  return SOURCES.find(s => s.id === id)?.label || 'Google Maps'
}

function selectSource(id) {
  source.value = id
  formError.value = ''
  formSuccess.value = ''
}

function selectType(id) {
  entityType.value = id
  formError.value = ''
}

async function startOp() {
  if (!subject.value.trim()) {
    formError.value = `Preencha ${currentType.value.subjectLabel.toLowerCase()}.`
    return
  }
  starting.value = true
  formError.value = ''
  formSuccess.value = ''
  try {
    await store.startOperation(source.value, {
      searchText: query.value,
      title: title.value.trim() || null,
      limit: limit.value || null,
    })
    formSuccess.value = 'Operação iniciada! Os leads serão coletados em breve.'
    subject.value = ''
    city.value = ''
    title.value = ''
  } catch (e) {
    formError.value = e.response?.data?.detail || 'Erro ao iniciar operação.'
  } finally {
    starting.value = false
  }
}

async function stopOp(op) {
  stopping.value = op.id_operation
  try {
    await store.stopOperation(op.id_operation, op.source)
  } finally {
    stopping.value = null
  }
}

// Modal com os leads de uma operação
const detail = ref(null)
const detailLeads = ref([])
const detailLoading = ref(false)
const detailError = ref('')

async function openDetail(op) {
  detail.value = op
  detailLeads.value = []
  detailError.value = ''
  detailLoading.value = true
  try {
    detailLeads.value = await store.fetchOperationLeads(op.id_operation)
  } catch (e) {
    detailError.value = e.response?.data?.detail || 'Erro ao carregar os leads.'
  } finally {
    detailLoading.value = false
  }
}

function closeDetail() {
  detail.value = null
}

function onDetailKeydown(e) {
  if (e.key === 'Escape') closeDetail()
}

onMounted(() => document.addEventListener('keydown', onDetailKeydown))
onUnmounted(() => document.removeEventListener('keydown', onDetailKeydown))
</script>

<template>
  <div class="space-y-8">
    <div>
      <h1 class="text-2xl font-extrabold text-txt-primary">Prospecção</h1>
      <p class="mt-1 text-sm text-txt-secondary">Escolha a fonte, descreva quem você procura e colete leads automaticamente.</p>
    </div>

    <!-- Form -->
    <div class="card">
      <h2 class="mb-5 font-semibold text-txt-primary">Nova operação</h2>
      <form @submit.prevent="startOp" class="space-y-5">
        <div>
          <label class="label">Fonte</label>
          <div class="flex gap-2">
            <button
              v-for="s in SOURCES"
              :key="s.id"
              type="button"
              @click="selectSource(s.id)"
              :class="[
                'rounded-xl border px-4 py-2 text-sm font-medium transition',
                source === s.id
                  ? 'border-brand/40 bg-brand/10 text-brand'
                  : 'border-brd-light text-txt-secondary hover:bg-surface-hover',
              ]"
            >
              {{ s.label }}
            </button>
          </div>
          <p class="mt-1.5 text-xs text-txt-secondary/60">{{ current.hint }}</p>
        </div>

        <div>
          <label class="label">Você procura</label>
          <div class="flex gap-2">
            <button
              v-for="t in ENTITY_TYPES"
              :key="t.id"
              type="button"
              @click="selectType(t.id)"
              :class="[
                'rounded-xl border px-4 py-2 text-sm font-medium transition',
                entityType === t.id
                  ? 'border-brand/40 bg-brand/10 text-brand'
                  : 'border-brd-light text-txt-secondary hover:bg-surface-hover',
              ]"
            >
              {{ t.label }}
            </button>
          </div>
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label class="label">{{ currentType.subjectLabel }} <span class="text-red-400">*</span></label>
            <input v-model="subject" type="text" :placeholder="currentType.placeholder" class="input" required />
            <div class="mt-2 flex flex-wrap gap-1.5">
              <button
                v-for="s in currentType.suggestions"
                :key="s"
                type="button"
                @click="subject = s"
                class="rounded-lg border border-brd-light px-2 py-1 text-[11px] text-txt-secondary transition hover:bg-surface-hover hover:text-txt-primary"
              >
                {{ s }}
              </button>
            </div>
          </div>
          <div>
            <label class="label">Título da operação (opcional)</label>
            <input v-model="title" type="text" placeholder="Ex: Vets Vitória" class="input" />
          </div>
        </div>

        <div>
          <label class="label">Quantos leads buscar</label>
          <div class="flex flex-wrap items-center gap-2">
            <input
              v-model.number="limit"
              type="number"
              min="1"
              placeholder="Sem limite"
              class="input w-36"
            />
            <button
              v-for="n in LIMIT_PRESETS"
              :key="n"
              type="button"
              @click="limit = n"
              :class="[
                'rounded-lg border px-3 py-1.5 text-xs font-medium transition',
                limit === n
                  ? 'border-brand/40 bg-brand/10 text-brand'
                  : 'border-brd-light text-txt-secondary hover:bg-surface-hover',
              ]"
            >
              {{ n }}
            </button>
            <button
              type="button"
              @click="limit = null"
              :class="[
                'rounded-lg border px-3 py-1.5 text-xs font-medium transition',
                !limit
                  ? 'border-brand/40 bg-brand/10 text-brand'
                  : 'border-brd-light text-txt-secondary hover:bg-surface-hover',
              ]"
            >
              Sem limite
            </button>
          </div>
          <p class="mt-1.5 text-xs text-txt-secondary/60">
            A operação encerra ao atingir esse número. Sem limite, ela vai até
            esgotar os resultados.
          </p>
        </div>

        <div>
          <label class="label">Região</label>
          <div class="flex gap-2">
            <button
              type="button"
              @click="limitRegion = true"
              :class="[
                'rounded-xl border px-4 py-2 text-sm font-medium transition',
                limitRegion
                  ? 'border-brand/40 bg-brand/10 text-brand'
                  : 'border-brd-light text-txt-secondary hover:bg-surface-hover',
              ]"
            >
              Definir região
            </button>
            <button
              type="button"
              @click="limitRegion = false"
              :class="[
                'rounded-xl border px-4 py-2 text-sm font-medium transition',
                !limitRegion
                  ? 'border-brand/40 bg-brand/10 text-brand'
                  : 'border-brd-light text-txt-secondary hover:bg-surface-hover',
              ]"
            >
              Sem limite
            </button>
          </div>

          <div v-if="limitRegion" class="mt-3 grid gap-3 sm:grid-cols-3">
            <div>
              <label class="label text-xs">País</label>
              <input type="text" value="Brasil" class="input" disabled />
            </div>
            <div>
              <label class="label text-xs">Estado (opcional)</label>
              <select v-model="uf" class="input">
                <option value="">Todos</option>
                <option v-for="u in UFS" :key="u.sigla" :value="u.sigla">{{ u.nome }}</option>
              </select>
            </div>
            <div>
              <label class="label text-xs">Cidade (opcional)</label>
              <input v-model="city" type="text" placeholder="Ex: Vitória" class="input" />
            </div>
          </div>
        </div>

        <div v-if="formError" class="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-2.5 text-sm text-red-400">{{ formError }}</div>
        <div v-if="formSuccess" class="rounded-xl bg-brand/10 border border-brand/20 px-4 py-2.5 text-sm text-brand">{{ formSuccess }}</div>

        <button type="submit" :disabled="starting" class="btn-primary">
          <svg v-if="starting" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ starting ? 'Iniciando…' : 'Iniciar operação' }}
        </button>
      </form>
    </div>

    <!-- Operações ativas -->
    <div class="card">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="font-semibold text-txt-primary">Em andamento</h2>
        <button @click="store.fetchOperations()" class="btn-secondary text-xs gap-1.5">
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Atualizar
        </button>
      </div>

      <div v-if="activeOps.length === 0" class="py-10 text-center">
        <svg class="mx-auto h-10 w-10 text-txt-secondary/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <p class="mt-2 text-sm text-txt-secondary/50">Nenhuma operação em andamento.</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="op in activeOps"
          :key="op.id_operation"
          class="flex items-center justify-between rounded-xl border border-brand/15 bg-brand/5 px-4 py-3"
        >
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <span class="relative flex h-2.5 w-2.5">
                <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand opacity-50"></span>
                <span class="relative inline-flex h-2.5 w-2.5 rounded-full bg-brand"></span>
              </span>
              <p class="text-sm font-medium text-txt-primary">{{ op.operation_name }}</p>
              <span class="badge-gray text-[10px]">{{ sourceLabel(op.source) }}</span>
            </div>
            <p class="mt-0.5 truncate pl-4 text-xs text-txt-secondary/60">{{ op.search_text }}</p>
          </div>
          <button
            @click="stopOp(op)"
            :disabled="stopping === op.id_operation"
            class="btn-danger ml-4 shrink-0 text-xs"
          >
            <svg v-if="stopping === op.id_operation" class="h-3.5 w-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            {{ stopping === op.id_operation ? 'Parando…' : 'Parar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Histórico -->
    <div v-if="inactiveOps.length > 0" class="card">
      <h2 class="mb-4 font-semibold text-txt-primary">Histórico</h2>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-brd-light">
              <th class="pb-3 text-left font-medium text-txt-secondary">Nome</th>
              <th class="pb-3 text-left font-medium text-txt-secondary">Fonte</th>
              <th class="pb-3 text-left font-medium text-txt-secondary">Busca</th>
              <th class="pb-3 text-left font-medium text-txt-secondary">Status</th>
              <th class="pb-3"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-brd-light">
            <tr
              v-for="op in inactiveOps"
              :key="op.id_operation"
              @click="openDetail(op)"
              class="cursor-pointer transition hover:bg-surface-hover"
            >
              <td class="py-3 font-medium text-txt-primary">{{ op.operation_name }}</td>
              <td class="py-3 text-txt-secondary">{{ sourceLabel(op.source) }}</td>
              <td class="py-3 text-txt-secondary">{{ op.search_text }}</td>
              <td class="py-3"><span class="badge-gray">Encerrada</span></td>
              <td class="py-3 text-right text-xs text-brand">Ver leads</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal: leads de uma operação -->
    <Teleport to="body">
      <div
        v-if="detail"
        @click.self="closeDetail"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      >
        <div class="flex max-h-[85vh] w-full max-w-4xl flex-col rounded-2xl border border-brd-light bg-surface shadow-2xl">
          <div class="flex items-start justify-between gap-4 border-b border-brd-light px-6 py-4">
            <div class="min-w-0">
              <h3 class="truncate font-semibold text-txt-primary">{{ detail.operation_name }}</h3>
              <p class="mt-0.5 truncate text-xs text-txt-secondary/70">
                {{ sourceLabel(detail.source) }} · {{ detail.search_text }}
              </p>
            </div>
            <button @click="closeDetail" class="btn-secondary shrink-0 text-xs">Fechar</button>
          </div>

          <div class="min-h-0 flex-1 overflow-auto px-6 py-4">
            <p v-if="detailLoading" class="py-10 text-center text-sm text-txt-secondary/60">
              Carregando…
            </p>

            <p v-else-if="detailError" class="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-2.5 text-sm text-red-400">
              {{ detailError }}
            </p>

            <div v-else-if="detailLeads.length === 0" class="py-10 text-center">
              <p class="text-sm text-txt-secondary/60">Nenhum lead vinculado a esta operação.</p>
              <p class="mt-1 text-xs text-txt-secondary/40">
                Operações anteriores a esta versão não registravam esse vínculo.
              </p>
            </div>

            <table v-else class="w-full text-sm">
              <thead>
                <tr class="border-b border-brd-light">
                  <th class="pb-2 text-left font-medium text-txt-secondary">Nome</th>
                  <th class="pb-2 text-left font-medium text-txt-secondary">Telefone</th>
                  <th class="pb-2 text-left font-medium text-txt-secondary">Site</th>
                  <th class="pb-2 text-left font-medium text-txt-secondary">Endereço</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-brd-light">
                <tr v-for="lead in detailLeads" :key="lead.id_lead">
                  <td class="py-2.5 font-medium text-txt-primary">{{ lead.nome }}</td>
                  <td class="py-2.5 text-txt-secondary">{{ lead.telefone || '—' }}</td>
                  <td class="py-2.5">
                    <a
                      v-if="lead.site"
                      :href="lead.site.startsWith('http') ? lead.site : `https://${lead.site}`"
                      target="_blank"
                      rel="noopener"
                      class="text-brand hover:underline"
                    >{{ lead.site }}</a>
                    <span v-else class="text-txt-secondary">—</span>
                  </td>
                  <td class="py-2.5 text-txt-secondary">{{ lead.endereco || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="!detailLoading && detailLeads.length" class="border-t border-brd-light px-6 py-3 text-xs text-txt-secondary/60">
            {{ detailLeads.length }} lead(s)
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
