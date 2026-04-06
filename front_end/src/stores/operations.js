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

  async function startOperation(searchText, messageUser, title) {
    const { data } = await api.post('/automations/operations/maps/activate', null, {
      params: { serach_text: searchText, message_user: messageUser, title },
    })
    operations.value = [data, ...operations.value]
  }

  async function stopOperation(id) {
    await api.put('/automations/operations/maps/deactivate', null, {
      params: { id_operation: id },
    })
    await fetchOperations()
  }

  return { operations, loading, error, fetchOperations, startOperation, stopOperation }
})
