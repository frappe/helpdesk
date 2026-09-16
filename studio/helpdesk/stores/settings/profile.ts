import { ref } from 'vue'
import { call, toast } from 'frappe-ui'

export function createProfileSettings(core) {
  // Form state, seeded from the server payload on every load.
  const profileFirstName = ref('')
  const profileLastName = ref('')
  const passwordOpen = ref(false)
  const currentPassword = ref('')
  const newPassword = ref('')

  core.afterLoad(() => {
    profileFirstName.value = core.settingsUser.value.first_name || ''
    profileLastName.value = core.settingsUser.value.last_name || ''
  })

  function saveProfile() {
    return core.run(
      () => call('helpdesk.api.organization.update_profile', {
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
      core.run(() => call('helpdesk.api.organization.update_profile', { image: fileUrl }), 'Photo updated')
    )
  }

  function removeProfileImage() {
    return core.run(() => call('helpdesk.api.organization.update_profile', { image: '' }), 'Photo removed')
  }

  function openPasswordChange() {
    currentPassword.value = ''
    newPassword.value = ''
    passwordOpen.value = true
  }

  function changePassword() {
    if (!currentPassword.value || !newPassword.value) {
      toast.error('Please fill in both passwords')
      return
    }
    return core.run(async () => {
      await call('frappe.core.doctype.user.user.update_password', {
        old_password: currentPassword.value,
        new_password: newPassword.value,
      })
      passwordOpen.value = false
    }, 'Password updated')
  }

  return {
    profileFirstName,
    profileLastName,
    passwordOpen,
    currentPassword,
    newPassword,
    openPasswordChange,
    changePassword,
    saveProfile,
    renameProfile,
    uploadProfileImage,
    removeProfileImage,
  }
}
