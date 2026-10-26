<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AuthShell from '@/components/auth/AuthShell.vue'
import FormAlert from '@/components/auth/FormAlert.vue'
import SubmitButton from '@/components/auth/SubmitButton.vue'
import { passwordProblem } from '@/components/auth/password'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const confirmation = ref('')
const error = ref('')
const loading = ref(false)

const mismatch = computed(
  () => confirmation.value.length > 0 && confirmation.value !== password.value
)

async function submit() {
  error.value = passwordProblem(password.value, confirmation.value)
  if (error.value) return

  loading.value = true
  try {
    await auth.register(email.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    const status = e.response?.status
    if (status === 409) {
      error.value = 'Já existe uma conta com este e-mail. Entre ou recupere a senha.'
    } else if (status === 422) {
      error.value = 'Confira o e-mail e a senha informados.'
    } else {
      error.value = 'Não foi possível criar a conta agora. Tente novamente.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell subtitle="Crie sua conta e faça a primeira busca">
    <form @submit.prevent="submit" class="card space-y-5">
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
        <label class="label" for="password">Senha</label>
        <input
          id="password"
          v-model="password"
          type="password"
          autocomplete="new-password"
          placeholder="Mínimo de 8 caracteres"
          minlength="8"
          required
          class="input"
        />
      </div>
      <div>
        <label class="label" for="confirmation">Confirme a senha</label>
        <input
          id="confirmation"
          v-model="confirmation"
          type="password"
          autocomplete="new-password"
          placeholder="••••••••"
          required
          class="input"
          :class="{ '!border-red-500/50': mismatch }"
        />
        <p v-if="mismatch" class="mt-1.5 text-xs text-red-400">As senhas não conferem.</p>
      </div>

      <FormAlert v-if="error">{{ error }}</FormAlert>

      <SubmitButton :loading="loading" label="Criar conta" loading-label="Criando conta…" />
    </form>

    <template #footer>
      Já tem conta?
      <RouterLink to="/login" class="font-medium text-brand hover:text-brand-hover">Entrar</RouterLink>
    </template>
  </AuthShell>
</template>
