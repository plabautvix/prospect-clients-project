<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useWhatsappStore } from '@/stores/whatsapp'

const store = useWhatsappStore()

onMounted(async () => {
  await store.fetchStatus()
  store.connectSSE()
  await store.fetchSentSummary()
  await store.fetchSentLog(50)
})

onUnmounted(() => store.disconnectSSE())

function formatTs(ts) {
  return new Date(ts).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}
</script>

<template>
  <div class="space-y-8">
    <div>
      <h1 class="text-2xl font-extrabold text-txt-primary">WhatsApp</h1>
      <p class="mt-1 text-sm text-txt-secondary">Gerencie a conexão com o WhatsApp e acompanhe os envios.</p>
    </div>

    <div class="grid gap-6 lg:grid-cols-2">
      <!-- Conexão -->
      <div class="card space-y-5">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold text-txt-primary">Status da conexão</h2>
          <span :class="[
            'badge',
            store.isReady ? 'badge-green' : store.qrDataUrl ? 'badge-yellow' : 'badge-gray'
          ]">
            {{ store.statusLabel }}
          </span>
        </div>

        <!-- Conectado -->
        <div v-if="store.isReady" class="flex flex-col items-center gap-3 py-8">
          <div class="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/15">
            <svg class="h-9 w-9 text-emerald-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
            </svg>
          </div>
          <p class="text-sm font-semibold text-txt-primary">WhatsApp conectado!</p>
          <p class="text-xs text-txt-secondary/60">A sessão está ativa. Você pode enviar mensagens.</p>
        </div>

        <!-- QR Code -->
        <div v-else-if="store.qrDataUrl" class="flex flex-col items-center gap-4">
          <p class="text-sm text-txt-secondary">Escaneie o QR Code com o WhatsApp do seu celular:</p>
          <div class="rounded-2xl bg-white p-3">
            <img :src="store.qrDataUrl" alt="QR Code do WhatsApp" class="w-56 h-56" />
          </div>
          <p class="text-xs text-txt-secondary/50">Abra o WhatsApp → Menu → Aparelhos conectados → Conectar um aparelho</p>
        </div>

        <!-- Aguardando -->
        <div v-else class="flex flex-col items-center gap-3 py-8">
          <div class="flex h-16 w-16 items-center justify-center rounded-full bg-surface-hover">
            <svg class="h-9 w-9 text-txt-secondary/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <p class="text-sm text-txt-secondary">Aguardando conexão…</p>
          <p class="text-xs text-txt-secondary/50">Certifique-se de que o serviço WhatsApp está rodando na porta 3001.</p>
        </div>

        <div v-if="store.authFailure" class="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-2.5 text-sm text-red-400">
          Falha de autenticação: {{ store.authFailure }}
        </div>
      </div>

      <!-- Estatísticas de envio -->
      <div class="card space-y-5">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold text-txt-primary">Estatísticas de envio</h2>
          <button @click="store.fetchSentSummary()" class="text-xs text-brand hover:text-brand-hover transition-colors">Atualizar</button>
        </div>

        <div class="grid grid-cols-3 gap-3">
          <div class="rounded-xl bg-surface-hover p-4 text-center">
            <p class="text-xs text-txt-secondary/60">Total</p>
            <p class="text-2xl font-extrabold text-txt-primary mt-1">{{ store.sentSummary.total }}</p>
          </div>
          <div class="rounded-xl bg-emerald-500/10 p-4 text-center">
            <p class="text-xs text-emerald-400">Enviadas</p>
            <p class="text-2xl font-extrabold text-emerald-400 mt-1">{{ store.sentSummary.sent }}</p>
          </div>
          <div class="rounded-xl bg-red-500/10 p-4 text-center">
            <p class="text-xs text-red-400">Falhas</p>
            <p class="text-2xl font-extrabold text-red-400 mt-1">{{ store.sentSummary.failed }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Histórico de envios -->
    <div class="card">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="font-semibold text-txt-primary">Histórico de envios</h2>
        <button @click="store.fetchSentLog()" class="btn-secondary text-xs">Atualizar</button>
      </div>

      <div v-if="store.sentLog.length === 0" class="py-10 text-center">
        <svg class="mx-auto h-10 w-10 text-txt-secondary/20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <p class="mt-2 text-sm text-txt-secondary/50">Nenhuma mensagem enviada ainda.</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="border-b border-brd-light">
            <tr>
              <th class="pb-3 text-left font-medium text-txt-secondary">Status</th>
              <th class="pb-3 text-left font-medium text-txt-secondary">Lead</th>
              <th class="pb-3 text-left font-medium text-txt-secondary hidden sm:table-cell">Telefone (JID)</th>
              <th class="pb-3 text-left font-medium text-txt-secondary hidden md:table-cell">Horário</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-brd-light">
            <tr v-for="(item, i) in store.sentLog" :key="i">
              <td class="py-3">
                <span :class="item.ok ? 'badge-green' : 'badge-red'">{{ item.ok ? 'OK' : 'Falha' }}</span>
              </td>
              <td class="py-3 font-medium text-txt-primary">{{ item.lead?.nome || '—' }}</td>
              <td class="py-3 text-txt-secondary/60 hidden sm:table-cell font-mono text-xs">{{ item.to }}</td>
              <td class="py-3 text-txt-secondary/50 hidden md:table-cell">{{ formatTs(item.ts) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
