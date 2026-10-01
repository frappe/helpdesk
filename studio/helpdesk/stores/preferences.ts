import { computed, ref } from 'vue'
import { useStorage } from '@vueuse/core'
import { createDocumentResource, createResource, toast } from 'frappe-ui'
import { __, fetchTranslations } from '@helpdesk/shared/translation'

// In the browser, not on the User doc: it describes this screen on this device.
const LAYOUT_KEY = 'kb:conversation-layout'
const LAYOUT_OPTIONS = [
  { label: 'Timeline', value: 'timeline' },
  { label: 'Chat', value: 'chat' },
]

const store = createPreferencesStore()

export function usePreferences() {
  return store
}

function createPreferencesStore() {
  const conversationLayout = useStorage(LAYOUT_KEY, 'timeline')

  const user = ref(null)
  const languageOptions = ref([])
  const timezoneOptions = ref([])

  const preferences = computed(() => user.value?.doc || {})
  const isPreferencesSaving = computed(() => Boolean(user.value?.save.loading))

  // Takes the User's docname: for Administrator that is not the email.
  function loadPreferences(userName) {
    if (!userName || user.value?.name === userName) return
    user.value = createDocumentResource({ doctype: 'User', name: userName })
    if (!languageOptions.value.length) languages.fetch()
    if (!timezoneOptions.value.length) timezones.fetch()
  }

  function setPreference(field, picked) {
    if (!user.value?.doc || isPreferencesSaving.value) return
    const value = picked || user.value.originalDoc?.[field]
    if (value === user.value.originalDoc?.[field]) return
    user.value.doc[field] = value
    savePreferences()
  }

  function savePreferences() {
    user.value?.save.submit(null, {
      onSuccess: () => {
        fetchTranslations()
        toast.success(__('Preferences updated successfully.'))
      },
      onError: (error) => toast.error(error.message),
    })
  }

  const languages = createResource({
    url: 'frappe.client.get_list',
    params: {
      doctype: 'Language',
      fields: ['name', 'language_name'],
      limit_page_length: 0,
      order_by: 'language_name asc',
    },
    onSuccess: (rows) =>
      (languageOptions.value = rows.map((row) => ({
        label: row.language_name || row.name,
        value: row.name,
      }))),
  })

  const timezones = createResource({
    url: 'frappe.core.doctype.user.user.get_timezones',
    onSuccess: (data) =>
      (timezoneOptions.value = data.timezones.map((zone) => ({ label: zone, value: zone }))),
  })

  return {
    conversationLayout,
    conversationLayoutOptions: computed(() =>
      LAYOUT_OPTIONS.map((option) => ({ ...option, label: __(option.label) })),
    ),
    preferences,
    languageOptions,
    timezoneOptions,
    loadPreferences,
    setPreference,
  }
}
