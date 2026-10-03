<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useCampaignsStore, CHANNELS, campaignPayload } from '@/stores/campaigns'

const props = defineProps({
  // Leads marcados à mão. Vazio significa "todos os leads do filtro".
  leadIds: { type: Array, default: () => [] },
  filters: { type: Object, default: () => ({}) },
  targetCount: { type: Number, required: true },
  defaultChannel: { type: String, default: 'whatsapp' },
})
const emit = defineEmits(['close', 'created'])

const store = useCampaignsStore()

const channel = ref(props.defaultChannel)
const name = ref('')
const template = ref('{Olá|Oi} {nome}, tudo bem?')

const preview = ref(null)
const previewLoading = ref(false)
const submitting = ref(false)
const error = ref(null)

const SKIP_REASONS = {
  sem_contato: { whatsapp: 'sem celular válido', instagram: 'não são perfis do Instagram' },
  nao_contatar: 'marcados como não contatar',
  ja_contatado: 'já contatados por este canal',
  duplicado: 'contato repetido na seleção',
}

const skippedList = computed(() => {
  if (!preview.value) return []
  return Object.entries(preview.value.skipped)
    .filter(([, total]) => total > 0)
    .map(([key, total]) => {
      const reason = SKIP_REASONS[key]
      return { total, label: typeof reason === 'string' ? reason : reason[channel.value] }
    })
})

const target = computed(() =>
  props.leadIds.length
    ? `${props.targetCount} lead(s) selecionado(s)`
    : `Todos os ${props.targetCount} leads do filtro atual`
)

function payload() {
  return campaignPayload({
    channel: channel.value,
    template: template.value,
    name: name.value.trim(),
    leadIds: props.leadIds,
    filters: props.filters,
  })
}

// A prévia vem do servidor: só ele sabe quem já foi contatado e quem pediu
// para não receber mensagem.
let timer = null
let requestId = 0
function schedulePreview() {
  clearTimeout(timer)
  if (!template.value.trim()) {
    preview.value = null
    return
  }
  timer = setTimeout(async () => {
    const id = ++requestId
    previewLoading.value = true
    error.value = null
    try {
      const data = await store.preview(payload())
      if (id === requestId) preview.value = data
    } catch (e) {
      if (id === requestId) error.value = e.response?.data?.detail || 'Erro ao gerar a prévia'
    } finally {
      if (id === requestId) previewLoading.value = false
    }
  }, 400)
}

watch([channel, template], schedulePreview)

async function submit() {
  submitting.value = true
  error.value = null
  try {
    const result = await store.create(payload())
    emit('created', result)
  } catch (e) {
    const detail = e.response?.data?.detail
    error.value = typeof detail === 'string' ? detail : 'Erro ao criar a campanha'
  } finally {
    submitting.value = false
  }
}

function onKeydown(e) {
  if (e.key === 'Escape') emit('close')
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  schedulePreview()
})
onUnmounted(() => {
  clearTimeout(timer)
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <div
      @click.self="emit('close')"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
    >
      <div class="flex max-h-[90vh] w-full max-w-3xl flex-col rounded-2xl border border-brd-light bg-surface shadow-2xl">
        <div class="flex items-start justify-between gap-4 border-b border-brd-light px-6 py-4">
          <div class="min-w-0">
            <h3 class="font-semibold text-txt-primary">Enviar mensagem</h3>
            <p class="mt-0.5 text-xs text-txt-secondary/70">{{ target }}</p>
          </div>
          <button @click="emit('close')" class="btn-secondary shrink-0 text-xs">Fechar</button>
        </div>

        <div class="min-h-0 flex-1 space-y-5 overflow-auto px-6 py-5">
          <div>
            <label class="label">Canal</label>
            <div class="flex gap-2">
              <button
                v-for="c in CHANNELS"
                :key="c.id"
                type="button"
                @click="channel = c.id"
                :class="[
                  'flex-1 rounded-xl border px-3 py-2 text-sm font-medium transition',
                  channel === c.id
                    ? 'border-brand/40 bg-brand/10 text-brand'
                    : 'border-brd-light text-txt-secondary hover:bg-surface-hover',
                ]"
              >
                {{ c.label }}
              </button>
            </div>
          </div>

          <div>
            <label class="label">Nome da campanha (opcional)</label>
            <input v-model="name" type="text" maxlength="255" placeholder="Ex.: Padarias Vitória" class="input" />
          </div>

          <div>
            <label class="label">Mensagem</label>
            <textarea v-model="template" rows="4" maxlength="1000" class="input resize-y" />
            <p class="mt-1.5 text-xs text-txt-secondary/60">
              Use <code class="text-brand">{nome}</code> e <code class="text-brand">{categoria}</code>.
              Para variar o texto entre os leads, escreva as opções entre chaves separadas por barra:
              <code class="text-brand">{Olá|Oi|E aí}</code>. Mensagens idênticas em massa chamam a atenção do filtro de spam.
            </p>
          </div>

          <!-- Prévia -->
          <div class="rounded-xl border border-brd-light bg-dark-base/40 p-4">
            <div class="flex items-center justify-between">
              <p class="text-sm font-medium text-txt-primary">Prévia</p>
              <span v-if="previewLoading" class="text-xs text-txt-secondary/60">Atualizando…</span>
            </div>

            <template v-if="preview">
              <p class="mt-2 text-sm text-txt-primary">
                <span class="font-semibold text-brand">{{ preview.eligible }}</span>
                {{ preview.eligible === 1 ? 'mensagem será enviada' : 'mensagens serão enviadas' }}
              </p>
              <ul v-if="skippedList.length" class="mt-1 space-y-0.5 text-xs text-txt-secondary/70">
                <li v-for="s in skippedList" :key="s.label">{{ s.total }} ignorado(s): {{ s.label }}</li>
              </ul>

              <div v-if="preview.samples.length" class="mt-3 space-y-2">
                <div
                  v-for="s in preview.samples"
                  :key="s.recipient"
                  class="rounded-lg border border-brd-light bg-surface px-3 py-2"
                >
                  <p class="text-[11px] text-txt-secondary/60">{{ s.nome }} · {{ s.recipient }}</p>
                  <p class="mt-0.5 whitespace-pre-wrap text-sm text-txt-primary">{{ s.body }}</p>
                </div>
              </div>
            </template>
            <p v-else-if="!previewLoading" class="mt-2 text-xs text-txt-secondary/60">
              Escreva a mensagem para ver a prévia.
            </p>
          </div>

          <p v-if="error" class="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2.5 text-sm text-red-400">
            {{ error }}
          </p>
        </div>

        <div class="flex items-center justify-between gap-4 border-t border-brd-light px-6 py-4">
          <p class="text-xs text-txt-secondary/60">
            As mensagens saem aos poucos, em lotes e em horário comercial, para não bloquear a conta.
          </p>
          <button
            class="btn-primary shrink-0"
            :disabled="submitting || previewLoading || !preview || preview.eligible === 0"
            @click="submit"
          >
            {{ submitting ? 'Enfileirando…' : `Enfileirar ${preview?.eligible ?? 0}` }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
