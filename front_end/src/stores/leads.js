import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/backend'

export const useLeadsStore = defineStore('leads', () => {
  const leads = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchLeads(skip = 0, limit = 200) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/leads/', { params: { skip, limit } })
      leads.value = data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Erro ao carregar leads'
    } finally {
      loading.value = false
    }
  }

  return { leads, loading, error, fetchLeads }
})
