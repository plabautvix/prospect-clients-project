const API_BASE_URL = "http://localhost:8000"
const WHATSAPP_API_URL = "http://localhost:3001"

export interface User {
  id: number
  email: string
  name: string
}

export interface Operation {
  id: number
  search_text: string
  message_user: string
  title?: string
  status: string
  created_at: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  name: string
}

export interface Lead {
  nome: string
  endereco: string
  telefone: string
  site?: string
}

export interface LeadsResponse {
  leads: Lead[]
  total: number
}

export const MOCK_OPERATIONS: Operation[] = [
  {
    id: 1,
    search_text: "Restaurantes em São Paulo",
    message_user: "Olá! Vi seu restaurante no Google Maps e gostaria de apresentar nossa solução de delivery.",
    title: "Prospecção Restaurantes SP",
    status: "running",
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 2,
    search_text: "Academias Rio de Janeiro",
    message_user: "Oi! Temos uma proposta especial para academias. Posso te contar mais?",
    title: "Prospecção Academias RJ",
    status: "completed",
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 3,
    search_text: "Salões de beleza Curitiba",
    message_user: "Olá! Trabalho com marketing digital para salões de beleza. Vamos conversar?",
    title: "Prospecção Salões Curitiba",
    status: "completed",
    created_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 4,
    search_text: "Pet shops Belo Horizonte",
    message_user: "Oi! Vi seu pet shop e adorei. Tenho uma parceria interessante para propor!",
    title: "Prospecção Pet Shops BH",
    status: "ativo",
    created_at: new Date(Date.now() - 30 * 60 * 60 * 1000).toISOString(),
  },
]

export function isMockUser(): boolean {
  if (typeof window === "undefined") return false
  const mockUser = localStorage.getItem("mock_user")
  return mockUser !== null
}

class ApiClient {
  private token: string | null = null

  constructor() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token")
    }
  }

  setToken(token: string) {
    this.token = token
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", token)
    }
  }

  clearToken() {
    this.token = null
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token")
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    }

    if (this.token) {
      ;(headers as Record<string, string>)["Authorization"] = `Bearer ${this.token}`
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Erro desconhecido" }))
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  // Auth endpoints
  async login(credentials: LoginCredentials) {
    const formData = new URLSearchParams()
    formData.append("username", credentials.username)
    formData.append("password", credentials.password)

    const response = await fetch(`${API_BASE_URL}/users/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Credenciais inválidas" }))
      throw new Error(error.detail || "Falha no login")
    }

    const data = await response.json()
    this.setToken(data.access_token)
    return data
  }

  async register(data: RegisterData) {
    return this.request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>("/users/userme")
  }

  // Operations endpoints
  async getOperations(): Promise<Operation[]> {
    if (isMockUser()) {
      return Promise.resolve(MOCK_OPERATIONS)
    }
    return this.request<Operation[]>("/automations/operations/")
  }

  async getOperation(id: number): Promise<Operation> {
    if (isMockUser()) {
      const op = MOCK_OPERATIONS.find((o) => o.id === id)
      if (op) return Promise.resolve(op)
    }
    return this.request<Operation>(`/automations/operations/${id}`)
  }

  async activateMapsService(searchText: string, messageUser: string, title?: string) {
    if (isMockUser()) {
      const newOp: Operation = {
        id: MOCK_OPERATIONS.length + 1,
        search_text: searchText,
        message_user: messageUser,
        title: title,
        status: "running",
        created_at: new Date().toISOString(),
      }
      MOCK_OPERATIONS.unshift(newOp)
      return Promise.resolve(newOp)
    }

    const params = new URLSearchParams({
      serach_text: searchText,
      message_user: messageUser,
    })
    if (title) {
      params.append("title", title)
    }

    return this.request(`/automations/operations/maps/activate?${params.toString()}`, {
      method: "POST",
    })
  }

  async deactivateMapsService(idOperation: number) {
    if (isMockUser()) {
      const op = MOCK_OPERATIONS.find((o) => o.id === idOperation)
      if (op) op.status = "parado"
      return Promise.resolve({ success: true })
    }

    const params = new URLSearchParams({
      id_operation: idOperation.toString(),
    })

    return this.request(`/automations/operations/maps/deactivate?${params.toString()}`, {
      method: "PUT",
    })
  }

  async deleteOperation(id: number) {
    if (isMockUser()) {
      const index = MOCK_OPERATIONS.findIndex((o) => o.id === id)
      if (index !== -1) MOCK_OPERATIONS.splice(index, 1)
      return Promise.resolve({ success: true })
    }

    return this.request(`/automations/operations/${id}`, {
      method: "DELETE",
    })
  }

  // Leads endpoints
  async searchLeads(query: string): Promise<LeadsResponse> {
    if (isMockUser()) {
      // Mock leads for testing
      return Promise.resolve({
        leads: [
          {
            nome: "Restaurante Sabor & Arte",
            endereco: "Rua das Flores, 123 - São Paulo",
            telefone: "11999887766",
            site: "www.saborarte.com.br",
          },
          {
            nome: "Pizzaria Bella Napoli",
            endereco: "Av. Brasil, 456 - São Paulo",
            telefone: "11988776655",
            site: "www.bellanapoli.com.br",
          },
          { nome: "Café Central", endereco: "Praça da República, 789 - São Paulo", telefone: "11977665544" },
        ],
        total: 3,
      })
    }

    const params = new URLSearchParams({ query })
    return this.request<LeadsResponse>(`/automations/leads?${params.toString()}`)
  }

  // WhatsApp endpoints
  async sendWhatsAppMessage(lead: Lead, message: string) {
    const response = await fetch(`${WHATSAPP_API_URL}/api/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lead, message }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: "Erro ao enviar mensagem" }))
      throw new Error(error.error || "Falha ao enviar mensagem")
    }

    return response.json()
  }

  async sendWhatsAppBatch(leads: Lead[], message: string) {
    const response = await fetch(`${WHATSAPP_API_URL}/api/send-batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ leads, message }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: "Erro ao enviar mensagens" }))
      throw new Error(error.error || "Falha ao enviar mensagens")
    }

    return response.json()
  }
}

export const apiClient = new ApiClient()

export { WHATSAPP_API_URL }
