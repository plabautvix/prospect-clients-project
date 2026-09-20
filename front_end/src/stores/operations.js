import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/backend'

export const useOperationsStore = defineStore('operations', () => {
  const operations = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchOperations() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/operations/')
      operations.value = data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Erro ao carregar operações'
    } finally {
      loading.value = false
    }
  }

  // The maps endpoint takes `serach_text` and a message template; the instagram
  // one takes `search_text` and no message, since nothing is sent yet.
  function activateParams(source, { searchText, messageUser, title }) {
    if (source === 'instagram') {
      return { search_text: searchText, title }
    }
    return { serach_text: searchText, message_user: messageUser, title }
  }

  async function startOperation(source, payload) {
    const { data } = await api.post(`/automations/operations/${source}/activate`, null, {
      params: activateParams(source, payload),
    })
    operations.value = [data, ...operations.value]
  }

  async function stopOperation(id, source = 'maps') {
    // Optimistic update: reflect the stop in the UI immediately.
    const op = operations.value.find((o) => o.id_operation === id)
    const previousStatus = op?.status
    if (op) op.status = 0
    try {
      await api.put(`/automations/operations/${source}/deactivate`, null, {
        params: { id_operation: id },
      })
      await fetchOperations()
    } catch (e) {
      // Revert the optimistic update if the request fails.
      if (op && previousStatus !== undefined) op.status = previousStatus
      throw e
    }
  }

  return { operations, loading, error, fetchOperations, startOperation, stopOperation }
})
