import { computed, nextTick, ref, watch } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { findBannerPreset } from '@helpdesk/shared/knowledgeBaseBanner'
import { readKnowledgeBasePreview } from '@helpdesk/shared/knowledgeBasePreview'
import { useSettingsModal } from '@app/stores/settings'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { ROUTES } from '@app/routes'

const ARTICLE_LIMIT = 5
const CATEGORY_GRID = '[data-component-id="Repeater-sxfnpzbam"]'
const EASE = 'cubic-bezier(0.2, 0, 0, 1)'

export default function setup(context) {
  const { articles, categories } = context
  const settings = useSettingsModal(context)
  const { config } = settings

  // Settings' Preview shows its unsaved banner and pins in place of the saved ones.
  // Read again with each session reload: saving the settings clears a stored preview.
  const preview = computed(() => config.value && readKnowledgeBasePreview())
  const bannerImage = computed(() => (preview.value ? preview.value.banner_image : config.value?.banner_image))

  // An uploaded image sits under a dark scrim, so it always takes white text.
  const bannerPreset = computed(() =>
    bannerImage.value ? null : findBannerPreset(preview.value ? preview.value.banner_preset : config.value?.banner_preset),
  )
  const bannerBackground = computed(() => bannerPreset.value?.background || '')
  const bannerTextColor = computed(() => (bannerImage.value ? '#fff' : 'var(--ink-gray-8)'))

  // Saving the knowledge base settings reloads the session; the pins come with the categories.
  watch(config, (_, previous) => previous && categories.reload())

  // Only the pinned categories, unless none are.
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

  // Animates the grid's height and the extra cards, which rise in from below and sink out before the grid shrinks.
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
    // Equal-height rows share the grid's height, so a height animation would squeeze every card.
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

  // A lone home category gets its own layout.
  const focusCategory = computed(() => (homeCategories.value.length === 1 ? homeCategories.value[0] : null))
  const isLoneCategory = computed(() => Boolean(focusCategory.value))

  // Waits for the categories: an earlier fetch could land after the right one.
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
    ...settings,
    ...useKnowledgeBaseHeader(context),
    bannerImage,
    bannerBackground,
    bannerTextColor,
    homeCategories,
    hasHiddenCategories,
    showAllCategories,
    gridCategories,
    toggleAllCategories,
    sort,
    focusCategory,
    isLoneCategory,
    articleRoute: ROUTES.article,
  }
}
