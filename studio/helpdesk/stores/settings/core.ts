import { ref, computed } from 'vue'
import { call, toast, FileUploadHandler } from 'frappe-ui'
import { usePreferences } from '@app/stores/preferences'
import { useSession } from '@app/stores/session'

// Tab state lives here so the organization module can watch it without depending on
// the dialog module that drives it.

export function createSettingsCore() {
  const settingsOpen = ref(false)
  const settingsTab = ref('profile') // 'profile' | 'members' | 'organization'
  const settingsData = ref(null)
  const settingsBusy = ref(false)

  const settingsUser = computed(() => settingsData.value?.user || {})
  const organizations = computed(() => settingsData.value?.organizations || [])
  const isAgentUser = computed(() => Boolean(settingsData.value?.is_agent))

  // The server enforces this; here it only decides whether the controls are worth drawing.
  const portalConfig = computed(() => useSession().config.value || {})

  const confirmAction = ref(null)
  // Apart from the options, so what is on the dialog survives its own closing animation.
  const confirmOpen = ref(false)

  function askConfirm(options) {
    confirmAction.value = options
    confirmOpen.value = true
  }

  function cancelConfirm() {
    confirmOpen.value = false
  }

  function acceptConfirm() {
    confirmOpen.value = false
    return confirmAction.value?.action?.()
  }

  // Modules that keep state derived from the payload re-seed themselves here.
  const reloadHooks = []
  function afterLoad(hook) {
    reloadHooks.push(hook)
  }

  async function loadSettings() {
    try {
      settingsData.value = await call('helpdesk.api.organization.get_settings')
      // By docname, not email: they differ for Administrator.
      usePreferences().loadPreferences(settingsUser.value.name)
      for (const hook of reloadHooks) await hook()
    } catch (error) {
      console.error(error)
      toast.error('Could not load settings')
    }
  }

  // `landed` covers actions that mail synchronously, where a mail failure fails a
  // request whose change is already saved.
  async function run(action, successMessage, landed) {
    if (settingsBusy.value) return
    settingsBusy.value = true
    try {
      await action()
      if (successMessage) toast.success(successMessage)
      await loadSettings()
    } catch (error) {
      console.error(error)
      await loadSettings()
      const partial = landed?.()
      if (partial) toast.warning(partial)
      else toast.error(serverMessage(error) || 'Something went wrong')
    } finally {
      settingsBusy.value = false
    }
  }

  function serverMessage(error) {
    return error?.messages?.[0] || error?.message
  }

  function pickImage(onUploaded) {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    input.onchange = async () => {
      const file = input.files && input.files[0]
      if (!file) return
      try {
        const uploaded = await new FileUploadHandler().upload(file, { private: false, optimize: true })
        await onUploaded(uploaded.file_url)
      } catch (error) {
        console.error(error)
        toast.error('Could not upload image')
      }
    }
    input.click()
  }

  return {
    settingsOpen,
    settingsTab,
    settingsData,
    settingsBusy,
    settingsUser,
    organizations,
    isAgentUser,
    portalConfig,
    confirmAction,
    confirmOpen,
    askConfirm,
    cancelConfirm,
    acceptConfirm,
    afterLoad,
    loadSettings,
    run,
    serverMessage,
    pickImage,
  }
}
