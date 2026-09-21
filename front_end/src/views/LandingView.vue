<script setup>
import LandingNav from '@/components/landing/LandingNav.vue'
import LandingHero from '@/components/landing/LandingHero.vue'
import LandingFooter from '@/components/landing/LandingFooter.vue'
</script>

<template>
  <div class="min-h-screen scroll-smooth bg-dark-base">
    <LandingNav />
    <main>
      <LandingHero />
    </main>
    <LandingFooter />
  </div>
</template>
