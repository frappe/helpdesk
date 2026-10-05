import { computed, ref } from 'vue'
import { call, createResource, toast } from 'frappe-ui'
import { __, fetchTranslations } from '@helpdesk/shared/translation'

export function createProfileSettings(core) {
  const passwordOpen = ref(false)
  const currentPassword = ref('')
  const newPassword = ref('')

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
    if (!languages.fetched) languages.fetch()
    if (!timezones.fetched) timezones.fetch()
  })

  function updateProfile(values, successMessage) {
    return core.run(() => call('helpdesk.api.auth.update_profile', values), successMessage)
  }

  function setPreference(field, value) {
    if (!value || value === core.settingsUser.value[field]) return
    return updateProfile({ [field]: value }, __('Preferences updated')).then(fetchTranslations)
  }

  // One field, two stored names: everything after the first space is the last name.
  function renameProfile(value) {
    const [firstName, ...rest] = value.split(/\s+/)
    return updateProfile({ first_name: firstName, last_name: rest.join(' ') }, __('Profile updated'))
  }

  function uploadProfileImage() {
    core.pickImage((fileUrl) => updateProfile({ image: fileUrl }, __('Photo updated')))
  }

  function removeProfileImage() {
    return updateProfile({ image: '' }, __('Photo removed'))
  }

  function openPasswordChange() {
    currentPassword.value = ''
    newPassword.value = ''
    passwordOpen.value = true
  }

  function changePassword() {
    if (!currentPassword.value || !newPassword.value) {
      return toast.error(__('Please fill in both passwords'))
    }
    return core.run(async () => {
      await call('frappe.core.doctype.user.user.update_password', {
        old_password: currentPassword.value,
        new_password: newPassword.value,
      })
      passwordOpen.value = false
    }, __('Password updated'))
  }

  return {
    passwordOpen,
    currentPassword,
    newPassword,
    openPasswordChange,
    changePassword,
    renameProfile,
    uploadProfileImage,
    removeProfileImage,
    languageOptions: computed(() => languages.data || []),
    timezoneOptions: computed(() => timezones.data || []),
    setPreference,
  }
}
