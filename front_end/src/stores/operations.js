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

  // The two endpoints spell the parameter differently. The message template is
  // no longer sent: the backend keeps a default, since nothing consumes the
  // queue yet.
  function activateParams(source, { searchText, title, limit }) {
    if (source === 'instagram') {
      return { search_text: searchText, title, limit }
    }
    return { serach_text: searchText, title, limit }
  }

  async function fetchOperationLeads(id) {
    const { data } = await api.get(`/operations/${id}/leads`)
    return data
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

  return {
    operations,
    loading,
    error,
    fetchOperations,
    fetchOperationLeads,
    startOperation,
    stopOperation,
  }
})
