<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  if (!email.value || !password.value) return
  loading.value = true
  error.value = ''
  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Credenciais inválidas.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-900 px-4">
    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="mb-8 flex flex-col items-center gap-3">
        <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600">
          <svg class="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div class="text-center">
          <h1 class="text-xl font-bold text-white">Prospect Clients</h1>
          <p class="mt-1 text-sm text-gray-400">Entre na sua conta para continuar</p>
        </div>
      </div>

      <form @submit.prevent="submit" class="space-y-4 rounded-xl bg-gray-800 p-6 shadow-xl">
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1">E-mail</label>
          <input
            v-model="email"
            type="email"
            placeholder="voce@exemplo.com"
            required
            class="block w-full rounded-lg border border-gray-600 bg-gray-700 px-3 py-2 text-sm text-white placeholder-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1">Senha</label>
          <input
            v-model="password"
            type="password"
            placeholder="••••••••"
            required
            class="block w-full rounded-lg border border-gray-600 bg-gray-700 px-3 py-2 text-sm text-white placeholder-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        <div v-if="error" class="rounded-lg bg-red-900/40 border border-red-700 px-3 py-2 text-sm text-red-300">
          {{ error }}
        </div>

        <button type="submit" :disabled="loading" class="btn-primary w-full">
          <svg v-if="loading" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          {{ loading ? 'Entrando…' : 'Entrar' }}
        </button>
      </form>
    </div>
  </div>
</template>
