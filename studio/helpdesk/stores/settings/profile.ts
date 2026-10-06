import { computed, ref } from 'vue'
import { call, createResource } from 'frappe-ui'
import { __, fetchTranslations } from '@helpdesk/shared/translation'

export function createProfileSettings(core) {
  const profileFirstName = ref('')
  const profileLastName = ref('')

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

  core.afterLoad(() => {
    profileFirstName.value = core.settingsUser.value.first_name || ''
    profileLastName.value = core.settingsUser.value.last_name || ''
    if (!languages.fetched) languages.fetch()
    if (!timezones.fetched) timezones.fetch()
  })

  function setPreference(field, value) {
    if (!value || value === core.settingsUser.value[field]) return
    return core
      .run(() => call('helpdesk.api.auth.update_profile', { [field]: value }), __('Preferences updated successfully.'))
      .then(fetchTranslations)
  }

  function saveProfile() {
    return core.run(
      () => call('helpdesk.api.auth.update_profile', {
        first_name: profileFirstName.value,
        last_name: profileLastName.value,
      }),
      'Profile updated'
    )
  }

  // One field, two stored names: everything after the first space is the last name.
  function renameProfile(value) {
    const [first, ...rest] = value.split(/\s+/)
    profileFirstName.value = first
    profileLastName.value = rest.join(' ')
    return saveProfile()
  }

  function uploadProfileImage() {
    core.pickImage((fileUrl) =>
      core.run(() => call('helpdesk.api.auth.update_profile', { image: fileUrl }), 'Photo updated')
    )
  }

  function removeProfileImage() {
    return core.run(() => call('helpdesk.api.auth.update_profile', { image: '' }), 'Photo removed')
  }

  return {
    renameProfile,
    uploadProfileImage,
    removeProfileImage,
    languageOptions: computed(() => languages.data || []),
    timezoneOptions: computed(() => timezones.data || []),
    setPreference,
  }
}
