import { ref } from 'vue'
import { call, toast } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'

export function createProfileSettings(core) {
  const passwordOpen = ref(false)
  const currentPassword = ref('')
  const newPassword = ref('')

  function updateProfile(values, successMessage) {
    return core.run(() => call('helpdesk.api.auth.update_profile', values), successMessage)
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
  }
}
