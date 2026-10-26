<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AuthShell from '@/components/auth/AuthShell.vue'
import FormAlert from '@/components/auth/FormAlert.vue'
import SubmitButton from '@/components/auth/SubmitButton.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref(route.query.email || '')
const password = ref('')
const error = ref('')
const loading = ref(false)

// Vindo da redefinição de senha.
const notice = route.query.redefinida ? 'Senha redefinida. Entre com a nova senha.' : ''

async function submit() {
  if (!email.value || !password.value) return
  loading.value = true
  error.value = ''
  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.status === 400
      ? 'E-mail ou senha incorretos.'
      : 'Não foi possível entrar agora. Tente novamente.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell subtitle="Entre na sua conta para continuar">
    <form @submit.prevent="submit" class="card space-y-5">
      <FormAlert v-if="notice && !error" kind="success">{{ notice }}</FormAlert>

      <div>
        <label class="label" for="email">E-mail</label>
        <input
          id="email"
          v-model="email"
          type="email"
          autocomplete="email"
          placeholder="voce@exemplo.com"
          required
          class="input"
        />
      </div>
      <div>
        <div class="mb-1.5 flex items-baseline justify-between">
          <label class="label !mb-0" for="password">Senha</label>
          <RouterLink
            :to="{ path: '/esqueci-senha', query: email ? { email } : {} }"
            class="text-xs text-txt-secondary transition-colors hover:text-brand"
          >Esqueci minha senha</RouterLink>
        </div>
        <input
          id="password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          placeholder="••••••••"
          required
          class="input"
        />
      </div>

      <FormAlert v-if="error">{{ error }}</FormAlert>

      <SubmitButton :loading="loading" label="Entrar" loading-label="Entrando…" />
    </form>

    <template #footer>
      Ainda não tem conta?
      <RouterLink to="/cadastro" class="font-medium text-brand hover:text-brand-hover">Criar conta</RouterLink>
    </template>
  </AuthShell>
</template>
