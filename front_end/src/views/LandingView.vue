<script setup>
import LandingNav from '@/components/landing/LandingNav.vue'
import LandingHero from '@/components/landing/LandingHero.vue'
import LandingSteps from '@/components/landing/LandingSteps.vue'
import LandingFeatures from '@/components/landing/LandingFeatures.vue'
import LandingSecurity from '@/components/landing/LandingSecurity.vue'
import LandingFaq from '@/components/landing/LandingFaq.vue'
import LandingCta from '@/components/landing/LandingCta.vue'
import LandingFooter from '@/components/landing/LandingFooter.vue'
</script>

<template>
  <div class="min-h-screen scroll-smooth bg-dark-base">
    <LandingNav />
    <main>
      <LandingHero />
      <LandingSteps />
      <LandingFeatures />
      <LandingSecurity />
      <LandingFaq />
      <LandingCta />
    </main>
    <LandingFooter />
  </div>
</template>
