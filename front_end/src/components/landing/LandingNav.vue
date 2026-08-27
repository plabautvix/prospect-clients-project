<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const links = [
  { label: 'Como funciona', href: '#como-funciona' },
  { label: 'Recursos', href: '#recursos' },
  { label: 'Segurança', href: '#seguranca' },
  { label: 'FAQ', href: '#faq' },
]

const scrolled = ref(false)
const open = ref(false)
const progress = ref(0)
const activeIndex = ref(-1)

// Pílula que desliza atrás do link da seção em que a página está.
const linkEls = ref([])
const indicator = ref({ left: '0px', width: '0px', opacity: 0 })

function setLinkRef(el, i) {
  if (el) linkEls.value[i] = el
}

function measure() {
  const el = linkEls.value[activeIndex.value]
  // offsetParent nulo = lista escondida no mobile; nada a marcar.
  if (!el || el.offsetParent === null) {
    indicator.value = { ...indicator.value, opacity: 0 }
    return
  }
  indicator.value = { left: `${el.offsetLeft}px`, width: `${el.offsetWidth}px`, opacity: 1 }
}

let ticking = false

function read() {
  scrolled.value = window.scrollY > 24

  const doc = document.documentElement
  const max = doc.scrollHeight - doc.clientHeight
  progress.value = max > 0 ? Math.min(1, window.scrollY / max) : 0

  let current = -1
  links.forEach((link, i) => {
    const section = document.querySelector(link.href)
    if (section && section.getBoundingClientRect().top <= 140) current = i
  })

  if (current !== activeIndex.value) {
    activeIndex.value = current
    nextTick(measure)
  } else {
    measure()
  }
}

function onScroll() {
  if (ticking) return
  ticking = true
  requestAnimationFrame(() => {
    read()
    ticking = false
  })
}

onMounted(() => {
  read()
  window.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('resize', onScroll)
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', onScroll)
})
</script>

<template>
  <header class="fixed inset-x-0 top-0 z-50 px-4 pt-4">
    <nav
      class="relative mx-auto flex max-w-5xl items-center gap-2 overflow-hidden rounded-pill border px-3 py-2 transition-[background-color,border-color,box-shadow,backdrop-filter] duration-500 ease-out"
      :class="scrolled
        ? 'border-brd-light bg-[#212523]/70 shadow-[0_10px_40px_-16px_rgba(16,229,128,0.45)] backdrop-blur-xl'
        : 'border-transparent bg-transparent shadow-none backdrop-blur-none'"
    >
      <!-- Fio de luz no topo da pílula -->
      <span
        class="pointer-events-none absolute inset-x-10 top-0 h-px bg-gradient-to-r from-transparent via-brand/60 to-transparent transition-opacity duration-500"
        :class="scrolled ? 'opacity-100' : 'opacity-0'"
        aria-hidden="true"
      ></span>

      <RouterLink to="/" class="group flex items-center gap-2 px-3 text-lg font-extrabold tracking-tight">
        <span
          class="h-2 w-2 rounded-full bg-brand transition-all duration-500"
          :class="scrolled ? 'shadow-[0_0_12px_2px_rgba(16,229,128,0.7)]' : 'shadow-none'"
        ></span>
        <span><span class="text-brand">Pr</span><span class="text-txt-primary">ospect</span></span>
      </RouterLink>

      <ul class="relative ml-2 hidden flex-1 items-center gap-1 md:flex">
        <!-- Indicador deslizante -->
        <li
          class="pointer-events-none absolute inset-y-0 rounded-pill bg-brand/10 ring-1 ring-inset ring-brand/25 transition-all duration-300 ease-out"
          :style="indicator"
          aria-hidden="true"
        ></li>

        <li v-for="(link, i) in links" :key="link.href" class="relative">
          <a
            :ref="(el) => setLinkRef(el, i)"
            :href="link.href"
            class="block rounded-pill px-3 py-2 text-sm transition-colors duration-300"
            :class="activeIndex === i ? 'text-brand' : 'text-txt-secondary hover:text-txt-primary'"
          >{{ link.label }}</a>
        </li>
      </ul>

      <div class="ml-auto flex items-center gap-2 md:ml-0">
        <template v-if="auth.isAuthenticated">
          <RouterLink to="/dashboard" class="btn-primary text-sm">Ir para o app</RouterLink>
        </template>
        <template v-else>
          <RouterLink
            to="/login"
            class="hidden rounded-pill px-3 py-2 text-sm text-txt-secondary transition-colors hover:bg-surface-hover hover:text-txt-primary sm:block"
          >Entrar</RouterLink>
          <RouterLink to="/login" class="btn-primary text-sm">Começar agora</RouterLink>
        </template>

        <button
          class="rounded-pill p-2 text-txt-secondary transition-colors hover:bg-surface-hover hover:text-txt-primary md:hidden"
          :aria-expanded="open"
          aria-label="Abrir menu"
          @click="open = !open"
        >
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-width="2" :d="open ? 'M6 18L18 6M6 6l12 12' : 'M4 7h16M4 12h16M4 17h16'" />
          </svg>
        </button>
      </div>

      <!-- Progresso de leitura, rente à borda de baixo -->
      <span
        class="pointer-events-none absolute bottom-0 left-0 h-px bg-brand transition-opacity duration-500"
        :class="scrolled ? 'opacity-80' : 'opacity-0'"
        :style="{ width: progress * 100 + '%' }"
        aria-hidden="true"
      ></span>
    </nav>

    <!-- Menu mobile -->
    <div
      v-show="open"
      class="mx-auto mt-2 max-w-5xl rounded-2xl border border-brd-light bg-[#191c1a]/95 p-2 backdrop-blur-md md:hidden"
    >
      <a
        v-for="link in links"
        :key="link.href"
        :href="link.href"
        class="block rounded-pill px-4 py-2.5 text-sm text-txt-secondary transition-colors hover:bg-surface-hover hover:text-txt-primary"
        @click="open = false"
      >{{ link.label }}</a>
    </div>
  </header>
</template>
