import { computed, ref, watch } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { findBannerPreset } from '@helpdesk/shared/knowledgeBaseBanner'
import { readKnowledgeBasePreview } from '@helpdesk/shared/knowledgeBasePreview'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { useRememberedCount } from '@app/composables/useRememberedCount'
import { homeCategoryColumns, prefetchOnHover } from '@app/stores/knowledgeBase'

// home lists show this many; the server caps Featured at MAX_PINNED_ARTICLES (hd_article.py)
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
      pinnedArticles.fetch(names ? { names: JSON.stringify(names) } : {})
    },
    { immediate: true },
  )

  // Subcategories open from their parent's page.
  const topCategories = computed(() => (categories.data || []).filter((row) => !row.parent_article_category))

  const pickedCategories = computed(() => {
    const rows = topCategories.value
    const order = preview.value?.pinned
    const pinned = order
      ? rows.filter((row) => order.includes(row.name)).sort((a, b) => order.indexOf(a.name) - order.indexOf(b.name))
      : rows.filter((row) => row.pinned).sort((a, b) => a.pinned_order - b.pinned_order)
    return pinned.length ? pinned : rows
  })

  // A lone category with two or more subcategories shows them as its cards; with one, it stays lone.
  const homeCategories = computed(() => {
    const rows = pickedCategories.value
    if (rows.length !== 1) return rows
    const subcategories = (categories.data || []).filter((row) => row.parent_article_category === rows[0].name)
    return subcategories.length > 1 ? subcategories : rows
  })

  const hasHiddenCategories = computed(() => pickedCategories.value.length < topCategories.value.length)

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

  // Pins swap Latest for Featured, which leads; a lone category has no tabs, so lists them above its own.
  const hasFeatured = computed(() => !focusCategory.value && Boolean(pinnedArticles.data?.length))
  const hasLoneFeatured = computed(() => Boolean(focusCategory.value && pinnedArticles.data?.length))
  const sortOptions = computed(() =>
    hasFeatured.value
      ? [
          { label: __('Featured'), value: 'featured' },
          { label: __('Popular'), value: 'popular' },
        ]
      : [
          { label: __('Popular'), value: 'popular' },
          { label: __('Latest'), value: 'latest' },
        ],
  )
  // A pick whose tab went away falls back to the first tab.
  const pickedSort = ref(null)
  const sort = computed({
    get: () =>
      sortOptions.value.some((option) => option.value === pickedSort.value)
        ? pickedSort.value
        : sortOptions.value[0].value,
    set: (value) => (pickedSort.value = value),
  })
  const homeArticles = computed(() => (sort.value === 'featured' ? pinnedArticles.data : articles.data))

  // Waits for categories and pins: an earlier fetch could land after the right one.
  const pinsSettled = computed(() => Boolean(pinnedArticles.data || pinnedArticles.error))
  // One picked category lists its own and its subcategories' articles, whether or not they show as cards.
  const branchCategory = computed(() => (pickedCategories.value.length === 1 ? pickedCategories.value[0] : null))
  watch(
    [sort, branchCategory, focusCategory, () => categories.data, pinsSettled],
    ([value, category, focus, loaded, settled]) => {
      if (!loaded || !settled || value === 'featured') return
      if (!category) return articles.fetch({ limit: ARTICLE_LIMIT, sort: value })
      // A pinned lone category previews like the rest; a site's only category lists everything.
      const limit = focus && !hasHiddenCategories.value ? 0 : ARTICLE_LIMIT
      articles.fetch({ category: category.name, include_subcategories: 1, limit, sort: value })
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
    homeCategoryColumns,
    skeletonCount,
    hasHiddenCategories,
    sort,
    sortOptions,
    homeArticles,
    focusCategory,
    isLoneCategory,
    hasLoneFeatured,
  }
}
