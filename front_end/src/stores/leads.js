import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/backend'

const EMPTY_FILTERS = { nome: '', categoria: [], telefone: '', endereco: '', site: '', origem: [] }

export const useLeadsStore = defineStore('leads', () => {
  const leads = ref([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(50)
  const filters = ref({ ...EMPTY_FILTERS })
  const categories = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchLeads() {
    loading.value = true
    error.value = null
    try {
      const params = {
        skip: (page.value - 1) * pageSize.value,
        limit: pageSize.value,
      }
      // Inclui apenas filtros preenchidos (arrays só quando têm itens)
      for (const [key, value] of Object.entries(filters.value)) {
        if (Array.isArray(value)) {
          if (value.length) params[key] = value
        } else if (value && value.trim()) {
          params[key] = value.trim()
        }
      }
      // Serializa arrays como chave repetida (categoria=a&categoria=b) p/ o FastAPI
      const { data } = await api.get('/leads/', {
        params,
        paramsSerializer: { indexes: null },
      })
      leads.value = data.items
      total.value = data.total
    } catch (e) {
      error.value = e.response?.data?.detail || 'Erro ao carregar leads'
    } finally {
      loading.value = false
    }
  }

  async function fetchCategories() {
    try {
      const { data } = await api.get('/leads/categories')
      categories.value = data
    } catch (e) {
      // Sugestões de categoria são auxiliares; falha não bloqueia a tela.
      categories.value = []
    }
  }

  function setPage(n) {
    const totalPages = Math.max(1, Math.ceil(total.value / pageSize.value))
    page.value = Math.min(Math.max(1, n), totalPages)
    return fetchLeads()
  }

  function setFilters(newFilters) {
    filters.value = { ...EMPTY_FILTERS, ...newFilters }
    page.value = 1
    return fetchLeads()
  }

  return {
    leads,
    total,
    page,
    pageSize,
    filters,
    categories,
    loading,
    error,
    fetchLeads,
    fetchCategories,
    setPage,
    setFilters,
  }
})
