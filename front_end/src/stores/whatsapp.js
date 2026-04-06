import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import whatsappApi from '@/services/whatsapp'
import QRCode from 'qrcode'

export const useWhatsappStore = defineStore('whatsapp', () => {
  const isReady = ref(false)
  const isAuthenticated = ref(false)
  const qrDataUrl = ref(null)
  const authFailure = ref(null)
  const sentSummary = ref({ total: 0, sent: 0, failed: 0 })
  const sentLog = ref([])

  let eventSource = null

  const statusLabel = computed(() => {
    if (isReady.value) return 'Conectado'
    if (isAuthenticated.value) return 'Autenticado'
    if (qrDataUrl.value) return 'Aguardando QR'
    return 'Desconectado'
  })

  async function connectSSE() {
    if (eventSource) return
    eventSource = new EventSource('http://localhost:3001/api/whatsapp/stream')

    eventSource.addEventListener('ready', (e) => {
      isReady.value = JSON.parse(e.data)
      if (isReady.value) qrDataUrl.value = null
    })
    eventSource.addEventListener('authenticated', (e) => {
      isAuthenticated.value = JSON.parse(e.data)
      if (isAuthenticated.value) qrDataUrl.value = null
    })
    eventSource.addEventListener('qr', async (e) => {
      const qrString = e.data
      qrDataUrl.value = await QRCode.toDataURL(qrString, { width: 280, margin: 2 })
      isReady.value = false
      isAuthenticated.value = false
    })
    eventSource.addEventListener('auth_failure', (e) => {
      authFailure.value = e.data
    })
    eventSource.addEventListener('disconnected', () => {
      isReady.value = false
      isAuthenticated.value = false
    })
  }

  function disconnectSSE() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }

  async function fetchStatus() {
    try {
      const { data } = await whatsappApi.get('/api/whatsapp/status')
      isReady.value = data.ready
      isAuthenticated.value = data.authenticated
    } catch (_) {}
  }

  async function fetchSentSummary() {
    try {
      const { data } = await whatsappApi.get('/api/sent/summary')
      sentSummary.value = data
    } catch (_) {}
  }

  async function fetchSentLog(limit = 50) {
    try {
      const { data } = await whatsappApi.get('/api/sent/log', { params: { limit } })
      sentLog.value = data.items
    } catch (_) {}
  }

  async function sendBatch(leads, message) {
    const { data } = await whatsappApi.post('/api/send-batch', { leads, message })
    await fetchSentSummary()
    return data
  }

  return {
    isReady, isAuthenticated, qrDataUrl, authFailure,
    sentSummary, sentLog, statusLabel,
    connectSSE, disconnectSSE, fetchStatus,
    fetchSentSummary, fetchSentLog, sendBatch,
  }
})
