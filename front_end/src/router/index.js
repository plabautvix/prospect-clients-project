import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'landing',
    component: () => import('@/views/LandingView.vue'),
    meta: { public: true },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true, guestOnly: true },
  },
  {
    path: '/cadastro',
    name: 'cadastro',
    component: () => import('@/views/RegisterView.vue'),
    meta: { public: true, guestOnly: true },
  },
  {
    path: '/esqueci-senha',
    name: 'esqueci-senha',
    component: () => import('@/views/ForgotPasswordView.vue'),
    meta: { public: true, guestOnly: true },
  },
  {
    // Aberta mesmo com sessão: o link do e-mail tem que funcionar sempre.
    path: '/redefinir-senha',
    name: 'redefinir-senha',
    component: () => import('@/views/ResetPasswordView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: 'dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
      { path: 'prospeccao', name: 'prospeccao', component: () => import('@/views/ProspeccaoView.vue') },
      { path: 'leads', name: 'leads', component: () => import('@/views/LeadsView.vue') },
      { path: 'campanhas', name: 'campanhas', component: () => import('@/views/CampanhasView.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  // Âncoras da landing (#recursos, #faq...) rolam suave; o resto volta ao topo.
  scrollBehavior(to, from, savedPosition) {
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return savedPosition ?? { top: 0 }
  },
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) return '/login'
  if (to.meta.guestOnly && auth.isAuthenticated) return '/dashboard'
})

export default router
