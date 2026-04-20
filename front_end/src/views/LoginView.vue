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
  <div class="flex min-h-screen items-center justify-center bg-dark-base px-4">
    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="mb-10 flex flex-col items-center gap-3">
        <h1 class="text-4xl font-extrabold tracking-tight">
          <span class="text-brand">Pr</span><span class="text-txt-primary">ospect</span>
        </h1>
        <p class="text-sm text-txt-secondary">Entre na sua conta para continuar</p>
      </div>

      <form @submit.prevent="submit" class="card space-y-5">
        <div>
          <label class="label">E-mail</label>
          <input
            v-model="email"
            type="email"
            placeholder="voce@exemplo.com"
            required
            class="input"
          />
        </div>
        <div>
          <label class="label">Senha</label>
          <input
            v-model="password"
            type="password"
            placeholder="••••••••"
            required
            class="input"
          />
        </div>

        <div v-if="error" class="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-2.5 text-sm text-red-400">
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
