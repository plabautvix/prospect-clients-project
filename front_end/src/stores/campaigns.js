import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/backend'

export const CHANNELS = [
  { id: 'whatsapp', label: 'WhatsApp' },
  { id: 'instagram', label: 'Instagram' },
]

export function channelLabel(id) {
  return CHANNELS.find((c) => c.id === id)?.label || id
}

// O backend aceita os mesmos filtros da listagem de leads. Campos vazios
// ficam de fora para não virarem filtro por string vazia.
function cleanFilters(filters) {
  const out = {}
  for (const [key, value] of Object.entries(filters || {})) {
    if (Array.isArray(value)) {
      if (value.length) out[key] = value
    } else if (value && value.trim()) {
      out[key] = value.trim()
    }
  }
  return out
}

// Alvo da campanha: os leads marcados à mão, ou tudo o que o filtro mostra.
export function campaignPayload({ channel, template, name, leadIds, filters }) {
  const payload = { channel, template, name: name || null }
  if (leadIds?.length) payload.lead_ids = leadIds
  else payload.filters = cleanFilters(filters)
  return payload
}

export const useCampaignsStore = defineStore('campaigns', () => {
  const campaigns = ref([])
  const channels = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchCampaigns() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/campaigns')
      campaigns.value = data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Erro ao carregar campanhas'
    } finally {
      loading.value = false
    }
  }

  async function fetchChannels() {
    try {
      const { data } = await api.get('/channels')
      channels.value = data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Erro ao carregar canais'
    }
  }

  // Por categoria: quantos leads uma campanha neste canal alcançaria.
  async function fetchAudience(channel) {
    const { data } = await api.get('/campaigns/audience', { params: { channel } })
    return data
  }

  async function preview(payload) {
    const { data } = await api.post('/campaigns/preview', payload)
    return data
  }

  async function create(payload) {
    const { data } = await api.post('/campaigns', payload)
    campaigns.value = [data.campaign, ...campaigns.value]
    return data
  }

  function replace(campaign) {
    const i = campaigns.value.findIndex((c) => c.id_campaign === campaign.id_campaign)
    if (i !== -1) campaigns.value[i] = campaign
  }

  async function pause(id) {
    const { data } = await api.post(`/campaigns/${id}/pause`)
    replace(data)
  }

  async function resume(id) {
    const { data } = await api.post(`/campaigns/${id}/resume`)
    replace(data)
  }

  async function cancel(id) {
    const { data } = await api.post(`/campaigns/${id}/cancel`)
    replace(data)
  }

  async function fetchMessages(id, { status, skip = 0, limit = 50 } = {}) {
    const { data } = await api.get(`/campaigns/${id}/messages`, {
      params: { status: status || undefined, skip, limit },
    })
    return data
  }

  // O backend não fala com o gateway: o pedido fica gravado e o worker
  // reinicia a sessão no próximo ciclo, em poucos segundos.
  async function reconnectChannel(channel) {
    const { data } = await api.post(`/channels/${channel}/reconnect`)
    const i = channels.value.findIndex((c) => c.channel === channel)
    if (i !== -1) channels.value[i] = data
  }

  // Código que o Instagram mandou por e-mail ou SMS. Segue o mesmo caminho
  // do pedido de QR: o worker o pega no próximo ciclo.
  async function submitVerificationCode(channel, code) {
    const { data } = await api.post(`/channels/${channel}/verification-code`, { code })
    const i = channels.value.findIndex((c) => c.channel === channel)
    if (i !== -1) channels.value[i] = data
  }

  async function unpauseChannel(channel) {
    await api.post(`/channels/${channel}/unpause`)
    await fetchChannels()
  }

  async function setDoNotContact(leadIds, value = true) {
    const { data } = await api.post('/leads/do-not-contact', {
      lead_ids: leadIds,
      nao_contatar: value,
    })
    return data.updated
  }

  return {
    campaigns,
    channels,
    loading,
    error,
    fetchCampaigns,
    fetchChannels,
    fetchAudience,
    preview,
    create,
    pause,
    resume,
    cancel,
    fetchMessages,
    reconnectChannel,
    submitVerificationCode,
    unpauseChannel,
    setDoNotContact,
  }
})
