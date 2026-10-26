import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/backend'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const userEmail = ref(localStorage.getItem('userEmail') || null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(email, password) {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)

    const { data } = await api.post('/users/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })

    token.value = data.access_token
    localStorage.setItem('token', data.access_token)

    const me = await api.get('/users/userme')
    userEmail.value = me.data.email
    localStorage.setItem('userEmail', me.data.email)
  }

  // Cria a conta e já entra nela.
  async function register(email, password) {
    await api.post('/users/', { email, password })
    await login(email, password)
  }

  // A resposta é sempre a mesma, exista a conta ou não.
  async function forgotPassword(email) {
    const { data } = await api.post('/users/password/forgot', { email })
    return data.message
  }

  async function resetPassword(resetToken, password) {
    await api.post('/users/password/reset', { token: resetToken, password })
  }

  function logout() {
    token.value = null
    userEmail.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userEmail')
  }

  return {
    token,
    userEmail,
    isAuthenticated,
    login,
    register,
    forgotPassword,
    resetPassword,
    logout,
  }
})
