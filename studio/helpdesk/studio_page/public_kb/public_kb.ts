import { computed, ref, watch } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { findBannerPreset } from '@helpdesk/shared/kbBanner'
import { readKbPreview } from '@helpdesk/shared/kbPreview'
import { useSettingsModal } from '@app/stores/settings'
import { useKbHeader } from '@app/composables/useKbHeader'
import { countLabel } from '@app/utils'

const ARTICLE_LIMIT = 5

export default function setup(context) {
  const { articles, categories } = context
  const settings = useSettingsModal(context)
  const { config } = settings

  // Settings' Preview shows its unsaved banner and pins in place of the saved ones.
  const preview = readKbPreview()
  const bannerImage = computed(() => (preview ? preview.banner_image : config.value?.banner_image))

  // An uploaded image sits under a dark scrim, so it always takes white text.
  const bannerPreset = computed(() =>
    bannerImage.value ? null : findBannerPreset(preview ? preview.banner_preset : config.value?.banner_preset),
  )
  const bannerBackground = computed(() => bannerPreset.value?.background || '')
  const bannerTextColor = computed(() => (bannerImage.value ? '#fff' : 'var(--ink-gray-8)'))

  // Saving the knowledge base settings reloads the session; the pins come with the categories.
  watch(config, (_, previous) => previous && categories.reload())

  // Only the pinned categories, unless none are.
  const homeCategories = computed(() => {
    const rows = categories.data || []
    const pinned = rows.filter((row) => (preview ? preview.pinned.includes(row.name) : row.pinned))
    return pinned.length ? pinned : rows
  })

  const hasHiddenCategories = computed(() => homeCategories.value.length < (categories.data || []).length)

  // One or two home categories get their own layouts.
  const fewCategories = computed(() => (homeCategories.value.length <= 2 ? homeCategories.value : []))
  const hasCategoryPicker = computed(() => fewCategories.value.length === 2)
  const pickedName = ref(null)
  const focusCategory = computed(
    () => fewCategories.value.find((row) => row.name === pickedName.value) || fewCategories.value[0] || null,
  )
  const isLoneCategory = computed(() => Boolean(focusCategory.value && !hasCategoryPicker.value))

  function pickCategory(name) {
    pickedName.value = name
  }

  function articleCount(category) {
    return countLabel(category.article_count, __('1 article'), __('{0} articles'))
  }

  // Waits for the categories: an earlier fetch could land after the right one.
  const sort = ref('latest')
  watch(
    [sort, focusCategory, () => categories.data],
    ([value, category, loaded]) => {
      if (!loaded) return
      if (!category) return articles.fetch({ limit: ARTICLE_LIMIT, sort: value })
      const limit = isLoneCategory.value ? 0 : ARTICLE_LIMIT
      articles.fetch({ category: category.name, limit, sort: value })
    },
    { immediate: true },
  )

  return {
    ...settings,
    ...useKbHeader(context),
    bannerImage,
    bannerBackground,
    bannerTextColor,
    homeCategories,
    hasHiddenCategories,
    sort,
    focusCategory,
    hasCategoryPicker,
    isLoneCategory,
    articleCount,
    pickCategory,
  }
}
