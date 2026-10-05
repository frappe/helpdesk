import { computed, ref } from 'vue'
import { createDocumentResource, createResource, toast } from 'frappe-ui'
import { __, fetchTranslations } from '@helpdesk/shared/translation'
import { errorMessage } from '@app/utils'

const store = createPreferencesStore()

export function usePreferences() {
  return store
}

function createPreferencesStore() {
  const user = ref(null)

  const preferences = computed(() => user.value?.doc || {})
  const isPreferencesSaving = computed(() => Boolean(user.value?.save.loading))

  const languages = createResource({
    url: 'frappe.client.get_list',
    params: {
      doctype: 'Language',
      fields: ['name', 'language_name'],
      limit_page_length: 0,
      order_by: 'language_name asc',
    },
    transform: (rows) => rows.map((row) => ({ label: row.language_name || row.name, value: row.name })),
  })

  const timezones = createResource({
    url: 'frappe.core.doctype.user.user.get_timezones',
    transform: (data) => data.timezones.map((zone) => ({ label: zone, value: zone })),
  })

  // Takes the User's docname: for Administrator that is not the email.
  function loadPreferences(userName) {
    if (!userName || user.value?.name === userName) return
    user.value = createDocumentResource({ doctype: 'User', name: userName })
    if (!languages.data) languages.fetch()
    if (!timezones.data) timezones.fetch()
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
        toast.success(__('Preferences updated'))
      },
      onError: (error) => toast.error(errorMessage(error, __('Could not update preferences'))),
    })
  }

  return {
    preferences,
    languageOptions: computed(() => languages.data || []),
    timezoneOptions: computed(() => timezones.data || []),
    loadPreferences,
    setPreference,
  }
}
