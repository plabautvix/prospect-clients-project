<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

const nav = [
  { name: 'Dashboard',    to: '/dashboard',  icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { name: 'Prospecção',   to: '/prospeccao', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' },
  { name: 'Leads',        to: '/leads',      icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' },
  { name: 'Campanhas',    to: '/campanhas',  icon: 'M12 19l9 2-9-18-9 18 9-2zm0 0v-8' },
]

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <aside class="flex w-64 shrink-0 flex-col border-r border-brd-light bg-[#191c1a]">
    <!-- Logo -->
    <div class="flex h-16 items-center px-6">
      <span class="text-xl font-extrabold tracking-tight">
        <span class="text-brand">Pr</span><span class="text-txt-primary">ospect</span>
      </span>
    </div>

    <!-- Nav -->
    <nav class="flex-1 space-y-1 px-3 py-6">
      <RouterLink
        v-for="item in nav"
        :key="item.to"
        :to="item.to"
        class="group flex items-center gap-3 rounded-pill px-4 py-2.5 text-sm font-medium text-[#8a918c] transition-all duration-200 hover:bg-white/[0.06] hover:text-txt-primary"
        active-class="!bg-brand !text-black"
      >
        <svg class="h-5 w-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" :d="item.icon" />
        </svg>
        {{ item.name }}
      </RouterLink>
    </nav>

    <!-- User -->
    <div class="border-t border-brd-light px-3 py-4">
      <div class="flex items-center gap-3 rounded-pill px-4 py-2">
        <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-bold text-black">
          {{ auth.userEmail?.[0]?.toUpperCase() ?? 'U' }}
        </div>
        <div class="min-w-0 flex-1">
          <p class="truncate text-xs text-txt-secondary">{{ auth.userEmail }}</p>
        </div>
        <button @click="logout" class="shrink-0 text-txt-secondary hover:text-brand transition-colors" title="Sair">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </div>
    </div>
  </aside>
</template>
