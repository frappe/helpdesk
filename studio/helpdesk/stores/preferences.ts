import { computed, ref } from 'vue'
import { setLanguage, t } from '@app/stores/translations'
import { createDocumentResource, createResource, toast } from 'frappe-ui'

// Language and timezone live on the User doc, which a signed-in user may edit themselves.

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
  const layout = ref(readLayout())

  const conversationLayout = computed({
    get: () => layout.value,
    set: (value) => {
      layout.value = value
      writeLayout(value)
    },
  })

  // Created once the settings payload names the signed-in user.
  const user = ref(null)
  const languageOptions = ref([])
  const timezoneOptions = ref([])

  const preferences = computed(() => user.value?.doc || {})

  const preferencesSaving = computed(() => Boolean(user.value?.save.loading))

  // Takes the User's docname — for Administrator that is not the email.
  function loadPreferences(userName) {
    if (!userName || user.value?.name === userName) return
    user.value = createDocumentResource({ doctype: 'User', name: userName })
    if (!languageOptions.value.length) languages.fetch()
    if (!timezoneOptions.value.length) timezones.fetch()
  }

  // An empty pick falls back to the saved value, so a stray clear cannot blank the field.
  function setPreference(field, picked) {
    if (!user.value?.doc) return
    if (preferencesSaving.value) return
    const value = picked || user.value.originalDoc?.[field]
    if (value === user.value.originalDoc?.[field]) return
    user.value.doc[field] = value
    savePreferences()
  }

  function savePreferences() {
    user.value?.save.submit(null, {
      onSuccess: () => {
        // Every string goes through `t()`, so telling the translator is enough — no reload.
        setLanguage(user.value.doc.language)
        toast.success(t('Preferences updated successfully.'))
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
      LAYOUT_OPTIONS.map((option) => ({ ...option, label: t(option.label) })),
    ),
    preferences,
    preferencesSaving,
    languageOptions,
    timezoneOptions,
    loadPreferences,
    setPreference,
    savePreferences,
  }
}

function readLayout() {
  try {
    return window.localStorage.getItem(LAYOUT_KEY) || 'timeline'
  } catch {
    return 'timeline'
  }
}

function writeLayout(value: string) {
  try {
    window.localStorage.setItem(LAYOUT_KEY, value)
  } catch {
    // A browser that refuses storage still gets the layout it just picked, for this visit.
  }
}
