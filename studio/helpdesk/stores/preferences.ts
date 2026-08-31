import { computed, ref } from 'vue'
import { setLanguage, t } from '@app/stores/translations'
import { createDocumentResource, createResource, toast } from 'frappe-ui'

// Language & timezone for the signed-in user, shown in the settings dialog's Profile
// panel. Both live on the User doc, which a signed-in user may edit for themselves, so
// this talks to that doc directly rather than through helpdesk.api.organization.
// Theme is deliberately absent — the portal ships light only.

// How the ticket thread is laid out. Kept in the browser rather than on the User doc:
// it describes this screen on this device, and there is no field for it to live in.
const LAYOUT_KEY = 'kb-conversation-layout'
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

  // Writable, so the settings Select binds to it the way the theme picker binds to
  // frappe-ui's own `currentTheme`.
  const conversationLayout = computed({
    get: () => layout.value,
    set: (value) => {
      layout.value = value
      writeLayout(value)
    },
  })

  // The User doc resource, created once the settings payload names the signed-in user.
  const user = ref(null)
  const languageOptions = ref([])
  const timezoneOptions = ref([])

  const preferences = computed(() => user.value?.doc || {})

  // Autocomplete selects by option, not by value: handed the bare string the User doc
  // stores, it cannot match one, and the next change it emits is whichever option happens
  // to sit first in the list — which is how picking हिन्दी saved Afrikaans. These resolve
  // the saved value to the option that carries it.
  const languageOption = computed(() =>
    optionFor('language', languageOptions.value, preferences.value.language),
  )
  const timezoneOption = computed(() =>
    optionFor('time_zone', timezoneOptions.value, preferences.value.time_zone),
  )

  // The last option each picker was shown, kept because a save replaces the doc and for
  // an instant the value is gone. Handed nothing to match, Autocomplete selects its first
  // option and emits it — which is how changing language once moved the reader's timezone
  // to Africa/Algiers. Holding the previous option through that gap leaves it matched.
  const lastOption = {}

  function optionFor(field, options, value) {
    if (!value) return lastOption[field] || null
    const match = options.find((option) => option.value === value) || { label: value, value }
    lastOption[field] = match
    return match
  }
  const preferencesSaving = computed(() => Boolean(user.value?.save.loading))

  // Called from the settings store on load, so nothing is fetched until the dialog
  // opens. Takes the User's docname — for Administrator that is not the email.
  function loadPreferences(userName) {
    if (!userName || user.value?.name === userName) return
    user.value = createDocumentResource({ doctype: 'User', name: userName })
    if (!languageOptions.value.length) languages.fetch()
    if (!timezoneOptions.value.length) timezones.fetch()
  }

  // Autocomplete hands back the chosen option (or null on clear); an empty pick falls
  // back to the saved value so a stray clear cannot blank the field.
  //
  // Saved on the spot. Every other row in this panel — theme, conversation layout —
  // takes effect the moment it is chosen, so a Save button standing behind these two
  // asked the reader to confirm a choice they had already made.
  function setPreference(field, option) {
    if (!user.value?.doc) return
    // Not while a save is in flight. The doc is replaced as it lands, so for a moment the
    // other picker has no value to match and emits its first option instead — which,
    // saving on selection, quietly moved the reader to Africa/Algiers when they changed
    // language.
    if (preferencesSaving.value) return
    const value = option?.value || user.value.originalDoc?.[field]
    if (value === user.value.originalDoc?.[field]) return
    user.value.doc[field] = value
    savePreferences()
  }

  function savePreferences() {
    user.value?.save.submit(null, {
      onSuccess: () => {
        // The portal changes language in place — every string it draws goes through
        // `t()`, so telling the translator is enough. Reloading was the old way, and it
        // blanked the screen to say something the reader had just watched happen.
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
    languageOption,
    timezoneOption,
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
