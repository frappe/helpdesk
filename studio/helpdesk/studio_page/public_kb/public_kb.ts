import { computed, nextTick, ref, watch } from 'vue'
import { findBannerPreset } from '@helpdesk/shared/knowledgeBaseBanner'
import { readKnowledgeBasePreview } from '@helpdesk/shared/knowledgeBasePreview'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { prefetchOnHover } from '@app/stores/knowledgeBase'

const ARTICLE_LIMIT = 5
const CATEGORY_GRID = '[data-component-id="category-grid-repeater"]'
const EASE = 'cubic-bezier(0.2, 0, 0, 1)'
// How many categories the home page showed last time, so the skeleton takes the same layout.
const HOME_COUNT_KEY = 'helpdesk-kb-home-categories'

function readHomeCount() {
  try {
    return Number(localStorage.getItem(HOME_COUNT_KEY)) || 0
  } catch {
    return 0
  }
}

export default function setup(context) {
  const { articles, categories } = context
  const settings = useKnowledgeBaseHeader(context)
  const { config } = settings

  // Settings Preview overrides banner and pins; re-read on session reload.
  const preview = computed(() => config.value && readKnowledgeBasePreview())
  const bannerImage = computed(() => (preview.value ? preview.value.banner_image : config.value?.banner_image))

  // Uploaded images sit under a dark scrim, so take white text.
  const bannerPreset = computed(() =>
    bannerImage.value ? null : findBannerPreset(preview.value ? preview.value.banner_preset : config.value?.banner_preset),
  )
  const bannerBackground = computed(() => bannerPreset.value?.background || '')
  const bannerTextColor = computed(() => (bannerImage.value ? '#fff' : 'var(--ink-gray-8)'))

  // Saving KB settings reloads the session; pins come with categories.
  watch(config, (_, previous) => previous && categories.reload())

  const homeCategories = computed(() => {
    const rows = categories.data || []
    const order = preview.value?.pinned
    const pinned = order
      ? rows.filter((row) => order.includes(row.name)).sort((a, b) => order.indexOf(a.name) - order.indexOf(b.name))
      : rows.filter((row) => row.pinned).sort((a, b) => a.pinned_order - b.pinned_order)
    return pinned.length ? pinned : rows
  })

  const hasHiddenCategories = computed(() => homeCategories.value.length < (categories.data || []).length)

  const showAllCategories = ref(false)
  const gridCategories = computed(() => {
    if (!showAllCategories.value) return homeCategories.value
    const rest = (categories.data || []).filter((row) => !homeCategories.value.includes(row))
    return [...homeCategories.value, ...rest]
  })

  let isToggling = false
  async function toggleAllCategories() {
    const grid = document.querySelector<HTMLElement>(CATEGORY_GRID)
    if (!grid || matchMedia('(prefers-reduced-motion: reduce)').matches) {
      showAllCategories.value = !showAllCategories.value
      return
    }
    if (isToggling) return
    isToggling = true
    const extraCards = () => [...grid.children].slice(homeCategories.value.length)
    if (showAllCategories.value) {
      const fades = extraCards().map((card) => card.animate({ opacity: [1, 0], transform: ['none', 'translateY(8px)'] }, { duration: 150, easing: EASE, fill: 'forwards' }))
      await Promise.all(fades.map((fade) => fade.finished))
    }
    const from = grid.offsetHeight
    showAllCategories.value = !showAllCategories.value
    await nextTick()
    // Equal-height rows would squeeze every card during the height animation.
    grid.style.gridAutoRows = `${grid.firstElementChild?.getBoundingClientRect().height}px`
    grid.style.overflow = 'hidden'
    const resize = grid.animate({ height: [`${from}px`, `${grid.offsetHeight}px`] }, { duration: 300, easing: EASE })
    if (showAllCategories.value) {
      extraCards().forEach((card, index) =>
        card.animate(
          { opacity: [0, 1], transform: ['translateY(12px)', 'none'] },
          { duration: 300, delay: 60 + Math.min(index, 8) * 30, easing: EASE, fill: 'backwards' },
        ),
      )
    }
    await resize.finished
    grid.style.overflow = ''
    grid.style.gridAutoRows = ''
    isToggling = false
  }

  const skeletonCount = readHomeCount() || 6
  watch(
    () => categories.data && homeCategories.value.length,
    (count) => {
      if (!count) return
      try {
        localStorage.setItem(HOME_COUNT_KEY, String(count))
      } catch {}
    },
  )

  const focusCategory = computed(() => (homeCategories.value.length === 1 ? homeCategories.value[0] : null))
  const isLoneCategory = computed(() => Boolean(focusCategory.value))

  // Waits for categories: an earlier fetch could land after the right one.
  const sort = ref('latest')
  watch(
    [sort, focusCategory, () => categories.data],
    ([value, category, loaded]) => {
      if (!loaded) return
      if (!category) return articles.fetch({ limit: ARTICLE_LIMIT, sort: value })
      articles.fetch({ category: category.name, limit: 0, sort: value })
    },
    { immediate: true },
  )

  return {
    prefetchOnHover,
    ...settings,
    bannerImage,
    bannerBackground,
    bannerTextColor,
    homeCategories,
    skeletonCount,
    hasHiddenCategories,
    showAllCategories,
    gridCategories,
    toggleAllCategories,
    sort,
    focusCategory,
    isLoneCategory,
  }
}
