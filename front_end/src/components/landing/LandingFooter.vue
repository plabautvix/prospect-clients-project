<script setup>
const year = new Date().getFullYear()

const groups = [
  {
    title: 'Produto',
    links: [
      { label: 'Como funciona', href: '#como-funciona' },
      { label: 'Recursos', href: '#recursos' },
      { label: 'Segurança', href: '#seguranca' },
    ],
  },
  {
    title: 'Suporte',
    links: [
      { label: 'FAQ', href: '#faq' },
      { label: 'contato@prospect.app', href: 'mailto:contato@prospect.app' },
    ],
  },
]
</script>

<template>
  <footer class="border-t border-brd-light">
    <div class="section grid gap-10 py-14 sm:grid-cols-[1.5fr_1fr_1fr]">
      <div>
        <span class="text-xl font-extrabold tracking-tight">
          <span class="text-brand">Pr</span><span class="text-txt-primary">ospect</span>
        </span>
        <p class="mt-3 max-w-xs text-sm leading-relaxed text-txt-secondary">
          Prospecção automática a partir do Google Maps: encontra os negócios
          e organiza os contatos para você consultar e ligar.
        </p>
      </div>

      <div v-for="group in groups" :key="group.title">
        <p class="text-sm font-semibold text-txt-primary">{{ group.title }}</p>
        <ul class="mt-4 space-y-2.5">
          <li v-for="link in group.links" :key="link.label">
            <a :href="link.href" class="text-sm text-txt-secondary transition-colors hover:text-brand">{{ link.label }}</a>
          </li>
        </ul>
      </div>
    </div>

    <div class="section flex flex-col items-center justify-between gap-3 border-t border-brd-light py-6 text-xs text-txt-secondary/70 sm:flex-row">
      <p>© {{ year }} Prospect. Todos os direitos reservados.</p>
      <p>Feito para times que vivem de prospectar.</p>
    </div>
  </footer>
</template>
