import { computed, ref, watch } from 'vue'
import { findBannerPreset } from '@helpdesk/shared/knowledgeBaseBanner'
import { readKnowledgeBasePreview } from '@helpdesk/shared/knowledgeBasePreview'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { useRememberedCount } from '@app/composables/useRememberedCount'
import { prefetchOnHover } from '@app/stores/knowledgeBase'

const ARTICLE_LIMIT = 5
export default function setup(context) {
  const { articles, categories, pinnedArticles } = context
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

  // Featured articles: the preview's unsaved pins, else the saved ones.
  watch(
    config,
    (value) => {
      if (!value) return
      const names = preview.value?.pinned_articles
      const params = names ? { names: JSON.stringify(names) } : { pinned: 1 }
      pinnedArticles.fetch({ ...params, limit: ARTICLE_LIMIT })
    },
    { immediate: true },
  )

  // Subcategories open from their parent's page.
  const topCategories = computed(() => (categories.data || []).filter((row) => !row.parent_article_category))

  const homeCategories = computed(() => {
    const rows = topCategories.value
    const order = preview.value?.pinned
    const pinned = order
      ? rows.filter((row) => order.includes(row.name)).sort((a, b) => order.indexOf(a.name) - order.indexOf(b.name))
      : rows.filter((row) => row.pinned).sort((a, b) => a.pinned_order - b.pinned_order)
    return pinned.length ? pinned : rows
  })

  const hasHiddenCategories = computed(() => homeCategories.value.length < topCategories.value.length)

  // The skeleton takes the layout of last time's count.
  const skeletonCount = useRememberedCount(
    'helpdesk-kb-home-categories',
    () => categories.data && homeCategories.value.length,
    6,
  )

  // Nothing the reader may see: the page offers its own actions, so the header doesn't.
  // Until categories load, last visit's count decides, so an empty one doesn't flash search.
  const isEmptyKnowledgeBase = computed(() => (categories.data ? !categories.data.length : skeletonCount === 0))
  const pageActionLabel = computed(() => (isEmptyKnowledgeBase.value ? '' : settings.pageActionLabel.value))
  const showLogin = computed(() => settings.isGuest.value && !isEmptyKnowledgeBase.value)

  const focusCategory = computed(() => (homeCategories.value.length === 1 ? homeCategories.value[0] : null))
  const isLoneCategory = computed(() => Boolean(focusCategory.value))

  // Pins swap Latest for Featured, which leads; a lone category has no tabs, so none.
  const hasFeatured = computed(() => !focusCategory.value && Boolean(pinnedArticles.data?.length))
  const pickedSort = ref(null)
  const sort = computed({
    get: () => {
      const fallback = hasFeatured.value ? 'featured' : 'popular'
      const hidden = hasFeatured.value ? 'latest' : 'featured'
      return pickedSort.value && pickedSort.value !== hidden ? pickedSort.value : fallback
    },
    set: (value) => (pickedSort.value = value),
  })
  const homeArticles = computed(() => (sort.value === 'featured' ? pinnedArticles.data : articles.data))

  // Waits for categories and pins: an earlier fetch could land after the right one.
  const pinsSettled = computed(() => Boolean(pinnedArticles.data || pinnedArticles.error))
  watch(
    [sort, focusCategory, () => categories.data, pinsSettled],
    ([value, category, loaded, settled]) => {
      if (!loaded || !settled || value === 'featured') return
      if (!category) return articles.fetch({ limit: ARTICLE_LIMIT, sort: value })
      // A pinned lone category previews like the rest; a site's only category lists everything.
      const limit = hasHiddenCategories.value ? ARTICLE_LIMIT : 0
      articles.fetch({ category: category.name, limit, sort: value })
    },
    { immediate: true },
  )

  return {
    prefetchOnHover,
    ...settings,
    isEmptyKnowledgeBase,
    pageActionLabel,
    showLogin,
    bannerImage,
    bannerBackground,
    bannerTextColor,
    homeCategories,
    skeletonCount,
    hasHiddenCategories,
    sort,
    hasFeatured,
    homeArticles,
    focusCategory,
    isLoneCategory,
  }
}
