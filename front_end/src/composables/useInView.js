import { onBeforeUnmount, onMounted, ref } from 'vue'

/**
 * Marca `visible` como true na primeira vez que o elemento entra na viewport.
 * Usado para revelar seções e animar contadores da landing.
 */
export function useInView({ threshold = 0.2, rootMargin = '0px 0px -10% 0px' } = {}) {
  const el = ref(null)
  const visible = ref(false)
  let observer = null

  onMounted(() => {
    if (!el.value || typeof IntersectionObserver === 'undefined') {
      visible.value = true
      return
    }
    observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return
      visible.value = true
      observer.disconnect()
    }, { threshold, rootMargin })
    observer.observe(el.value)
  })

  onBeforeUnmount(() => observer?.disconnect())

  return { el, visible }
}
