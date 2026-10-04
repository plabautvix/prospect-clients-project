<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useCampaignsStore, channelLabel } from '@/stores/campaigns'

const store = useCampaignsStore()

const CAMPAIGN_STATUS = {
  running: { label: 'Enviando', badge: 'badge-brand' },
  paused: { label: 'Pausada', badge: 'badge-yellow' },
  completed: { label: 'Concluída', badge: 'badge-green' },
  cancelled: { label: 'Cancelada', badge: 'badge-gray' },
}

const MESSAGE_STATUS = {
  pending: { label: 'Na fila', badge: 'badge-gray' },
  sending: { label: 'Enviando', badge: 'badge-brand' },
  sent: { label: 'Enviada', badge: 'badge-green' },
  failed: { label: 'Falhou', badge: 'badge-red' },
  cancelled: { label: 'Cancelada', badge: 'badge-gray' },
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// O que mostrar sobre a conta de cada canal, na ordem em que importa:
// sem serviço, conta com problema, pausa, e só então o ritmo normal.
function channelState(c) {
  if (!c.worker_online) {
    return c.health === 'unknown'
      ? { label: 'Serviço de envio não iniciado', badge: 'badge-gray' }
      : { label: 'Serviço de envio offline', badge: 'badge-red' }
  }
  if (c.health === 'disconnected') return { label: 'Desconectado', badge: 'badge-yellow' }
  if (c.health === 'blocked') return { label: 'Bloqueado pela plataforma', badge: 'badge-red' }
  return { label: 'Conectado', badge: 'badge-green' }
}

function nextSendText(c) {
  if (c.queued === 0) return 'Nada na fila'
  if (!c.next_send_at) return 'Enviando agora'
  return `Próximo envio: ${formatDate(c.next_send_at)}`
}

function progress(c) {
  if (!c.total) return 0
  const done = c.counts.sent + c.counts.failed + c.counts.cancelled
  return Math.round((done / c.total) * 100)
}

// Mensagens de uma campanha, abertas sob demanda.
const expanded = ref(null)
const messages = reactive({ items: [], total: 0, status: '', loading: false })

async function loadMessages() {
  messages.loading = true
  try {
    const data = await store.fetchMessages(expanded.value, { status: messages.status, limit: 200 })
    messages.items = data.items
    messages.total = data.total
  } finally {
    messages.loading = false
  }
}

function toggleMessages(id) {
  if (expanded.value === id) {
    expanded.value = null
    return
  }
  expanded.value = id
  messages.status = ''
  loadMessages()
}

function filterMessages(status) {
  messages.status = status
  loadMessages()
}

const reconnecting = ref(null)
async function reconnect(channel) {
  reconnecting.value = channel
  try {
    await store.reconnectChannel(channel)
    // Busca logo o código novo em vez de esperar o próximo ciclo de 10s.
    setTimeout(store.fetchChannels, 4000)
  } finally {
    reconnecting.value = null
  }
}

const codes = reactive({})
async function sendCode(channel) {
  await store.submitVerificationCode(channel, codes[channel].trim())
  codes[channel] = ''
  // O worker digita o código e espera o Instagram responder.
  setTimeout(store.fetchChannels, 15000)
}

const busy = ref(null)
async function act(action, campaign) {
  if (action === 'cancel' && !confirm(`Cancelar "${campaign.name}"? O que ainda não saiu não será enviado.`)) {
    return
  }
  busy.value = campaign.id_campaign
  try {
    await store[action](campaign.id_campaign)
    await store.fetchChannels()
  } finally {
    busy.value = null
  }
}

function refresh() {
  store.fetchCampaigns()
  store.fetchChannels()
  if (expanded.value) loadMessages()
}

let timer = null
onMounted(() => {
  refresh()
  timer = setInterval(refresh, 10000)
})
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-extrabold text-txt-primary">Campanhas</h1>
      <p class="mt-1 text-sm text-txt-secondary">
        Mensagens enviadas em lote. Para criar uma, selecione leads na tela de Leads.
      </p>
    </div>

    <!-- Contas remetentes -->
    <div class="grid gap-4 md:grid-cols-2">
      <div v-for="c in store.channels" :key="c.channel" class="card space-y-3">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold text-txt-primary">{{ channelLabel(c.channel) }}</h2>
          <span :class="channelState(c).badge">{{ channelState(c).label }}</span>
        </div>

        <p v-if="c.health_detail && c.worker_online && c.health !== 'ok'" class="text-sm text-txt-secondary">
          {{ c.health_detail }}
        </p>

        <div v-if="c.qr_code && c.worker_online && !c.reconnect_pending" class="flex flex-col items-center gap-2 rounded-xl bg-white p-4">
          <img :src="c.qr_code" alt="QR code para conectar o WhatsApp" class="h-56 w-56" />
          <p class="text-center text-xs text-gray-600">
            No celular: WhatsApp, Dispositivos conectados, Conectar dispositivo.
            O código se renova sozinho.
          </p>
        </div>

        <!-- Sempre há uma saída quando a conta não está conectada: um QR
             expirado ou uma tentativa recusada pede uma sessão nova. -->
        <div
          v-if="c.channel === 'whatsapp' && c.worker_online && c.health === 'disconnected'"
          class="flex items-center justify-between gap-3"
        >
          <p class="text-xs text-txt-secondary/70">
            {{ c.reconnect_pending ? 'Gerando um novo QR code, aguarde alguns segundos…' : 'O código não funcionou ou não aparece?' }}
          </p>
          <button
            class="btn-secondary shrink-0 text-xs"
            :disabled="c.reconnect_pending || reconnecting === c.channel"
            @click="reconnect(c.channel)"
          >
            Gerar novo QR code
          </button>
        </div>

        <!-- Instagram: código de verificação do login, ou nova tentativa de
             entrar depois de corrigir o que o aviso acima pediu. -->
        <form
          v-if="c.channel === 'instagram' && c.worker_online && c.needs_code"
          class="flex gap-2"
          @submit.prevent="sendCode(c.channel)"
        >
          <input
            v-model="codes[c.channel]"
            type="text"
            inputmode="numeric"
            autocomplete="one-time-code"
            maxlength="20"
            placeholder="Código de verificação"
            class="input"
            :disabled="c.code_pending"
          />
          <button class="btn-primary shrink-0 text-xs" :disabled="c.code_pending || !codes[c.channel]?.trim()">
            {{ c.code_pending ? 'Enviando…' : 'Enviar código' }}
          </button>
        </form>
        <div
          v-else-if="c.channel === 'instagram' && c.worker_online && c.health === 'disconnected'"
          class="flex items-center justify-between gap-3"
        >
          <p class="text-xs text-txt-secondary/70">
            {{ c.reconnect_pending ? 'Tentando entrar, aguarde alguns segundos…' : 'Resolveu o que o aviso pede?' }}
          </p>
          <button
            class="btn-secondary shrink-0 text-xs"
            :disabled="c.reconnect_pending || reconnecting === c.channel"
            @click="reconnect(c.channel)"
          >
            Entrar novamente
          </button>
        </div>

        <div
          v-if="c.paused_until"
          class="flex items-center justify-between gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 px-3 py-2"
        >
          <p class="text-sm text-amber-400">Pausado até {{ formatDate(c.paused_until) }}</p>
          <button class="btn-secondary text-xs" @click="store.unpauseChannel(c.channel)">Retomar agora</button>
        </div>

        <div class="grid grid-cols-3 gap-3 text-center">
          <div class="rounded-xl bg-dark-base/40 py-2">
            <p class="text-lg font-bold text-txt-primary">{{ c.sent_today }}<span class="text-xs text-txt-secondary">/{{ c.daily_cap }}</span></p>
            <p class="text-[11px] text-txt-secondary/70">enviadas hoje</p>
          </div>
          <div class="rounded-xl bg-dark-base/40 py-2">
            <p class="text-lg font-bold text-txt-primary">{{ c.queued }}</p>
            <p class="text-[11px] text-txt-secondary/70">na fila</p>
          </div>
          <div class="flex items-center justify-center rounded-xl bg-dark-base/40 px-2 py-2">
            <p class="text-[11px] text-txt-secondary">{{ nextSendText(c) }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Campanhas -->
    <div v-if="store.loading && store.campaigns.length === 0" class="card py-16 text-center text-sm text-txt-secondary/50">
      Carregando…
    </div>
    <div v-else-if="store.campaigns.length === 0" class="card py-16 text-center">
      <p class="text-sm text-txt-secondary/60">Nenhuma campanha ainda.</p>
      <RouterLink to="/leads" class="btn-primary mt-4">Escolher leads</RouterLink>
    </div>

    <div v-else class="space-y-3">
      <div v-for="c in store.campaigns" :key="c.id_campaign" class="card space-y-3 p-5">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <h3 class="truncate font-semibold text-txt-primary">{{ c.name }}</h3>
              <span class="badge-blue">{{ channelLabel(c.channel) }}</span>
              <span :class="CAMPAIGN_STATUS[c.status]?.badge">{{ CAMPAIGN_STATUS[c.status]?.label }}</span>
            </div>
            <p class="mt-0.5 text-xs text-txt-secondary/60">Criada em {{ formatDate(c.created_at) }}</p>
          </div>
          <div class="flex gap-2">
            <button
              v-if="c.status === 'running'"
              class="btn-secondary text-xs"
              :disabled="busy === c.id_campaign"
              @click="act('pause', c)"
            >Pausar</button>
            <button
              v-if="c.status === 'paused'"
              class="btn-success text-xs"
              :disabled="busy === c.id_campaign"
              @click="act('resume', c)"
            >Retomar</button>
            <button
              v-if="c.status === 'running' || c.status === 'paused'"
              class="btn-danger text-xs"
              :disabled="busy === c.id_campaign"
              @click="act('cancel', c)"
            >Cancelar</button>
            <button class="btn-secondary text-xs" @click="toggleMessages(c.id_campaign)">
              {{ expanded === c.id_campaign ? 'Ocultar' : 'Mensagens' }}
            </button>
          </div>
        </div>

        <div>
          <div class="h-2 overflow-hidden rounded-full bg-dark-base/60">
            <div class="h-full rounded-full bg-brand transition-all" :style="{ width: `${progress(c)}%` }" />
          </div>
          <div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-txt-secondary">
            <span><b class="text-emerald-400">{{ c.counts.sent }}</b> enviadas</span>
            <span><b class="text-txt-primary">{{ c.counts.pending + c.counts.sending }}</b> na fila</span>
            <span v-if="c.counts.failed"><b class="text-red-400">{{ c.counts.failed }}</b> falharam</span>
            <span v-if="c.counts.cancelled"><b>{{ c.counts.cancelled }}</b> canceladas</span>
            <span class="ml-auto">{{ progress(c) }}% de {{ c.total }}</span>
          </div>
        </div>

        <!-- Mensagens -->
        <div v-if="expanded === c.id_campaign" class="border-t border-brd-light pt-3">
          <div class="mb-3 flex gap-2">
            <button
              v-for="f in [{ id: '', label: 'Todas' }, { id: 'failed', label: 'Falhas' }, { id: 'sent', label: 'Enviadas' }, { id: 'pending', label: 'Na fila' }]"
              :key="f.id"
              @click="filterMessages(f.id)"
              :class="[
                'rounded-pill border px-3 py-1 text-xs transition',
                messages.status === f.id
                  ? 'border-brand/40 bg-brand/10 text-brand'
                  : 'border-brd-light text-txt-secondary hover:bg-surface-hover',
              ]"
            >{{ f.label }}</button>
          </div>

          <p v-if="messages.loading && !messages.items.length" class="py-6 text-center text-xs text-txt-secondary/60">Carregando…</p>
          <p v-else-if="!messages.items.length" class="py-6 text-center text-xs text-txt-secondary/60">Nenhuma mensagem.</p>
          <div v-else class="max-h-96 overflow-auto">
            <table class="w-full text-sm">
              <tbody class="divide-y divide-brd-light">
                <tr v-for="m in messages.items" :key="m.id_message" class="align-top">
                  <td class="py-2 pr-3">
                    <p class="font-medium text-txt-primary">{{ m.nome }}</p>
                    <p class="text-xs text-txt-secondary/60">{{ m.recipient }}</p>
                  </td>
                  <td class="py-2 pr-3 text-xs text-txt-secondary">
                    <p class="line-clamp-2 whitespace-pre-wrap">{{ m.body }}</p>
                    <p v-if="m.last_error" class="mt-1 text-red-400">{{ m.last_error }}</p>
                  </td>
                  <td class="whitespace-nowrap py-2 text-right">
                    <span :class="MESSAGE_STATUS[m.status]?.badge">{{ MESSAGE_STATUS[m.status]?.label }}</span>
                    <p v-if="m.sent_at" class="mt-1 text-[11px] text-txt-secondary/60">{{ formatDate(m.sent_at) }}</p>
                  </td>
                </tr>
              </tbody>
            </table>
            <p v-if="messages.total > messages.items.length" class="pt-2 text-center text-xs text-txt-secondary/60">
              Mostrando {{ messages.items.length }} de {{ messages.total }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
