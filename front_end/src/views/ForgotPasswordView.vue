<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AuthShell from '@/components/auth/AuthShell.vue'
import FormAlert from '@/components/auth/FormAlert.vue'
import SubmitButton from '@/components/auth/SubmitButton.vue'

const auth = useAuthStore()
const route = useRoute()

const email = ref(route.query.email || '')
const sent = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  if (!email.value) return
  loading.value = true
  error.value = ''
  try {
    sent.value = await auth.forgotPassword(email.value)
  } catch (e) {
    error.value = e.response?.status === 422
      ? 'Informe um e-mail válido.'
      : 'Não foi possível enviar agora. Tente novamente.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell subtitle="Enviaremos um link para você escolher uma nova senha">
    <div v-if="sent" class="card space-y-5">
      <FormAlert kind="success">{{ sent }}</FormAlert>
      <p class="text-sm leading-relaxed text-txt-secondary">
        Confira a caixa de entrada e o spam de <strong class="text-txt-primary">{{ email }}</strong>.
        O link vale por 30 minutos e só funciona uma vez.
      </p>
      <button type="button" class="btn-secondary w-full" :disabled="loading" @click="submit">
        Enviar de novo
      </button>
    </div>

    <form v-else @submit.prevent="submit" class="card space-y-5">
      <div>
        <label class="label" for="email">E-mail da conta</label>
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

      <FormAlert v-if="error">{{ error }}</FormAlert>

      <SubmitButton :loading="loading" label="Enviar link" loading-label="Enviando…" />
    </form>

    <template #footer>
      Lembrou a senha?
      <RouterLink to="/login" class="font-medium text-brand hover:text-brand-hover">Entrar</RouterLink>
    </template>
  </AuthShell>
</template>
