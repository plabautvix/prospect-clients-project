<script setup>
import { ref, computed, onMounted } from 'vue'
import { useOperationsStore } from '@/stores/operations'

const store = useOperationsStore()

const SOURCES = [
  {
    id: 'maps',
    label: 'Google Maps',
    searchLabel: 'Busca no Google Maps',
    placeholder: 'Ex: barbearias em São Paulo',
    titlePlaceholder: 'Ex: Barbearias SP',
    hint: 'Coleta nome, telefone, endereço e site dos negócios encontrados.',
  },
  {
    id: 'instagram',
    label: 'Instagram',
    searchLabel: 'Perfil que você procura',
    placeholder: 'Ex: médica veterinária em Campinas',
    titlePlaceholder: 'Ex: Vets Campinas',
    hint: 'Busca perfis pelo índice do Google. Não acessa o Instagram e não envia mensagem.',
  },
]

const source = ref('maps')
const searchText = ref('')
const messageTemplate = ref('Olá {nome}! Vi seu negócio e gostaria de apresentar uma oportunidade.')
const title = ref('')
const formError = ref('')
const formSuccess = ref('')
const starting = ref(false)
const stopping = ref(null)

onMounted(() => store.fetchOperations())

const activeOps = computed(() => store.operations.filter(o => o.status === 1))
const inactiveOps = computed(() => store.operations.filter(o => o.status === 0))
const current = computed(() => SOURCES.find(s => s.id === source.value))
const needsMessage = computed(() => source.value === 'maps')

function sourceLabel(id) {
  return SOURCES.find(s => s.id === id)?.label || 'Google Maps'
}

function selectSource(id) {
  source.value = id
  formError.value = ''
  formSuccess.value = ''
}

async function startOp() {
  if (!searchText.value.trim()) {
    formError.value = 'Preencha a busca.'
    return
  }
  if (needsMessage.value && !messageTemplate.value.trim()) {
    formError.value = 'Preencha o modelo de mensagem.'
    return
  }
  starting.value = true
  formError.value = ''
  formSuccess.value = ''
  try {
    await store.startOperation(source.value, {
      searchText: searchText.value.trim(),
      messageUser: needsMessage.value ? messageTemplate.value.trim() : null,
      title: title.value.trim() || null,
    })
    formSuccess.value = 'Operação iniciada! Os leads serão coletados em breve.'
    searchText.value = ''
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

        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label class="label">{{ current.searchLabel }} <span class="text-red-400">*</span></label>
            <input v-model="searchText" type="text" :placeholder="current.placeholder" class="input" required />
          </div>
          <div>
            <label class="label">Título da operação (opcional)</label>
            <input v-model="title" type="text" :placeholder="current.titlePlaceholder" class="input" />
          </div>
        </div>
        <div v-if="needsMessage">
          <label class="label">Modelo de mensagem <span class="text-red-400">*</span></label>
          <textarea
            v-model="messageTemplate"
            rows="3"
            placeholder="Use {nome} para personalizar. Ex: Olá {nome}! Temos uma oferta especial."
            class="input resize-none"
          />
          <p class="mt-1.5 text-xs text-txt-secondary/60">Use <code class="rounded-md bg-surface-hover px-1.5 py-0.5 text-brand text-[11px]">{nome}</code> para inserir o nome do negócio automaticamente.</p>
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
            </tr>
          </thead>
          <tbody class="divide-y divide-brd-light">
            <tr v-for="op in inactiveOps" :key="op.id_operation">
              <td class="py-3 font-medium text-txt-primary">{{ op.operation_name }}</td>
              <td class="py-3 text-txt-secondary">{{ sourceLabel(op.source) }}</td>
              <td class="py-3 text-txt-secondary">{{ op.search_text }}</td>
              <td class="py-3"><span class="badge-gray">Encerrada</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
