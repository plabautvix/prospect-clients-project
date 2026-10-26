<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AuthShell from '@/components/auth/AuthShell.vue'
import FormAlert from '@/components/auth/FormAlert.vue'
import SubmitButton from '@/components/auth/SubmitButton.vue'
import { passwordProblem } from '@/components/auth/password'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const token = typeof route.query.token === 'string' ? route.query.token : ''
const password = ref('')
const confirmation = ref('')
const error = ref('')
const invalidLink = ref(!token)
const loading = ref(false)

// Tira o token da barra de endereço e do histórico do navegador: ele já está
// guardado acima, e quem abrir o histórico não deve conseguir usá-lo.
onMounted(() => {
  if (route.query.token) router.replace({ query: {} })
})

const mismatch = computed(
  () => confirmation.value.length > 0 && confirmation.value !== password.value
)

async function submit() {
  error.value = passwordProblem(password.value, confirmation.value)
  if (error.value) return

  loading.value = true
  try {
    await auth.resetPassword(token, password.value)
    // Uma sessão aberta era da senha antiga.
    auth.logout()
    router.push({ path: '/login', query: { redefinida: '1' } })
  } catch (e) {
    if (e.response?.status === 400) {
      invalidLink.value = true
    } else {
      error.value = 'Não foi possível redefinir agora. Tente novamente.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell subtitle="Escolha uma nova senha para a sua conta">
    <div v-if="invalidLink" class="card space-y-5">
      <FormAlert>Este link é inválido ou expirou.</FormAlert>
      <p class="text-sm leading-relaxed text-txt-secondary">
        Cada link vale por 30 minutos e só pode ser usado uma vez. Peça um novo
        para continuar.
      </p>
      <RouterLink to="/esqueci-senha" class="btn-primary w-full">Pedir novo link</RouterLink>
    </div>

    <form v-else @submit.prevent="submit" class="card space-y-5">
      <div>
        <label class="label" for="password">Nova senha</label>
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
        <label class="label" for="confirmation">Confirme a nova senha</label>
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

      <SubmitButton :loading="loading" label="Salvar nova senha" loading-label="Salvando…" />
    </form>

    <template #footer>
      <RouterLink to="/login" class="font-medium text-brand hover:text-brand-hover">Voltar para o login</RouterLink>
    </template>
  </AuthShell>
</template>
