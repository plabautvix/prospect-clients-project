<script setup>
import { ref, computed, onMounted } from 'vue'
import { useOperationsStore } from '@/stores/operations'

const store = useOperationsStore()

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

async function startOp() {
  if (!searchText.value.trim() || !messageTemplate.value.trim()) {
    formError.value = 'Preencha a busca e o modelo de mensagem.'
    return
  }
  starting.value = true
  formError.value = ''
  formSuccess.value = ''
  try {
    await store.startOperation(searchText.value.trim(), messageTemplate.value.trim(), title.value.trim() || null)
    formSuccess.value = 'Operação iniciada! Os leads serão coletados em breve.'
    searchText.value = ''
    title.value = ''
  } catch (e) {
    formError.value = e.response?.data?.detail || 'Erro ao iniciar operação.'
  } finally {
    starting.value = false
  }
}

async function stopOp(id) {
  stopping.value = id
  try {
    await store.stopOperation(id)
  } finally {
    stopping.value = null
  }
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Prospecção</h1>
      <p class="mt-1 text-sm text-gray-500">Inicie uma operação de busca no Google Maps e colete leads automaticamente.</p>
    </div>

    <!-- Form -->
    <div class="card">
      <h2 class="mb-4 font-semibold text-gray-900">Nova operação</h2>
      <form @submit.prevent="startOp" class="space-y-4">
        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label class="label">Busca no Google Maps <span class="text-red-500">*</span></label>
            <input v-model="searchText" type="text" placeholder="Ex: barbearias em São Paulo" class="input" required />
          </div>
          <div>
            <label class="label">Título da operação (opcional)</label>
            <input v-model="title" type="text" placeholder="Ex: Barbearias SP" class="input" />
          </div>
        </div>
        <div>
          <label class="label">Modelo de mensagem <span class="text-red-500">*</span></label>
          <textarea
            v-model="messageTemplate"
            rows="3"
            placeholder="Use {nome} para personalizar. Ex: Olá {nome}! Temos uma oferta especial."
            class="input resize-none"
            required
          />
          <p class="mt-1 text-xs text-gray-400">Use <code class="rounded bg-gray-100 px-1 text-gray-600">{nome}</code> para inserir o nome do negócio automaticamente.</p>
        </div>

        <div v-if="formError" class="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">{{ formError }}</div>
        <div v-if="formSuccess" class="rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-2 text-sm text-emerald-700">{{ formSuccess }}</div>

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
        <h2 class="font-semibold text-gray-900">Em andamento</h2>
        <button @click="store.fetchOperations()" class="btn-secondary text-xs gap-1.5">
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Atualizar
        </button>
      </div>

      <div v-if="activeOps.length === 0" class="py-10 text-center">
        <svg class="mx-auto h-10 w-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <p class="mt-2 text-sm text-gray-400">Nenhuma operação em andamento.</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="op in activeOps"
          :key="op.id_operation"
          class="flex items-center justify-between rounded-lg border border-emerald-100 bg-emerald-50 px-4 py-3"
        >
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <span class="relative flex h-2.5 w-2.5">
                <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                <span class="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
              </span>
              <p class="text-sm font-medium text-gray-900">{{ op.operation_name }}</p>
            </div>
            <p class="mt-0.5 truncate pl-4 text-xs text-gray-500">{{ op.search_text }}</p>
          </div>
          <button
            @click="stopOp(op.id_operation)"
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
      <h2 class="mb-4 font-semibold text-gray-900">Histórico</h2>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="pb-2 text-left font-medium text-gray-500">Nome</th>
              <th class="pb-2 text-left font-medium text-gray-500">Busca</th>
              <th class="pb-2 text-left font-medium text-gray-500">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="op in inactiveOps" :key="op.id_operation">
              <td class="py-2 font-medium text-gray-900">{{ op.operation_name }}</td>
              <td class="py-2 text-gray-500">{{ op.search_text }}</td>
              <td class="py-2"><span class="badge-gray">Encerrada</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
