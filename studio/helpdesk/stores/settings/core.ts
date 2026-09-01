import { ref, computed } from 'vue'
import { call, toast, FileUploadHandler } from 'frappe-ui'
import { usePreferences } from '@app/stores/preferences'
import { useSession } from '@app/stores/session'

// The settings modules' shared plumbing: the server payload, the busy/confirm
// machinery every mutating action runs through, and the dialog's open/tab state
// (state lives here so the organization module can watch the tab without
// depending on the dialog module that drives it).

export function createSettingsCore() {
  const settingsOpen = ref(false)
  const settingsTab = ref('profile') // 'profile' | 'members' | 'organization'
  const settingsData = ref(null)
  const settingsBusy = ref(false)

  const settingsUser = computed(() => settingsData.value?.user || {})
  const organizations = computed(() => settingsData.value?.organizations || [])
  const isAgentUser = computed(() => Boolean(settingsData.value?.is_agent))

  // Managing an organization takes two yeses: you manage *this* one, and the helpdesk
  // allows customer-side self-service at all (HD Settings, off by default — most
  // helpdesks keep user administration agent-side). The server enforces both
  // independently; these only decide whether the controls are worth drawing.
  const portalConfig = computed(() => useSession().config.value || {})

  // Destructive actions route through one dialog rather than window.confirm, the
  // way the agent portal's ConfirmDialog does.
  const confirmAction = ref(null)
  // Open state kept apart from the options, so what is on the dialog survives its own
  // closing animation. Clearing the options to close it meant every binding fell back to
  // its default on the way out — a role change, which asks in grey, turned red for the
  // length of the fade.
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
      // By docname, not email: they differ for Administrator, and keying by email
      // loaded a different User doc — so language and timezone never took effect.
      usePreferences().loadPreferences(settingsUser.value.name)
      for (const hook of reloadHooks) await hook()
    } catch (error) {
      console.error(error)
      toast.error('Could not load settings')
    }
  }

  /** `landed` is for actions that email as part of the same request: the notice is
   *  sent synchronously, so a mail failure fails the whole request even though the
   *  change is already saved. It re-checks the reloaded data and returns the wording
   *  for that case, or nothing if the action really did fail. */
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
