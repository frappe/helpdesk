import { computed } from 'vue'
import { useTheme } from 'frappe-ui'
import { usePreferences } from '@app/stores/preferences'
import { useSession } from '@app/stores/session'
import { t } from '@app/stores/translations'
import { createSettingsCore } from './core'
import { createOrganizationSettings } from './organization'
import { createProfileSettings } from './profile'
import { createSettingsDialog } from './dialog'

// Shared state + actions for the portal settings dialog, used by every page script
// via `useSettingsModal(context)`. The dialog itself is the `kb_settings` studio
// component, which binds to whatever the host page's script returns — so every page
// carrying it returns this store. Backed by helpdesk.api.organization.
//
// One instance for the whole app: per-call state would give each page a private copy,
// so a load on one would leave the others showing stale settings.
const core = createSettingsCore()
const organization = createOrganizationSettings(core)
const profile = createProfileSettings(core)
const dialog = createSettingsDialog(core, organization)

// Every page script imports this module, so calling it here applies the saved theme on
// load rather than only once the settings dialog renders the picker.
const { currentTheme, setTheme } = useTheme()

// Writable so the theme Select can bind to it two-way; frappe-ui persists the choice.
const theme = computed({
  get: () => currentTheme.value,
  set: setTheme,
})

const themeOptions = computed(() => [
  { label: t('Light'), value: 'light' },
  { label: t('Dark'), value: 'dark' },
  { label: t('System'), value: 'system' },
])

// The portal's own furniture, in the reader's language. Here rather than on a page
// because every page spreads this store, and the header is shared between them.
const words = computed(() => ({
  raiseTicket: t('Raise a ticket'),
  status: t('Status'),
  composerPrompt: t('Type a message'),
  solveAsk: t('Did this solve your issue?'),
  solveYes: t("Yes, it's fixed"),
  solveNo: t('No, still an issue'),
  feedbackTitle: t('Feedback Rating'),
}))

const store = {
  words,
  themeOptions,
  theme,
  // The settings dialog's own wording is bound through this rather than written into
  // the blocks, so the panel a reader opens to change their language is itself in it.
  t,
  settingsOpen: core.settingsOpen,
  settingsTab: core.settingsTab,
  settingsBusy: core.settingsBusy,
  settingsUser: core.settingsUser,
  organizations: core.organizations,
  isAgentUser: core.isAgentUser,
  // Pages that show organizations outside the dialog have to ask for them.
  loadSettings: core.loadSettings,
  confirmAction: core.confirmAction,
  confirmOpen: core.confirmOpen,
  askConfirm: core.askConfirm,
  cancelConfirm: core.cancelConfirm,
  acceptConfirm: core.acceptConfirm,
  ...organization,
  ...profile,
  ...dialog,
}

// Every page script goes through here, so the session store rides along rather than
// being wired into each one: the topbar it feeds is on every page too.
export function useSettingsModal(context) {
  if (context) store.bindRouter(context.router)
  return { ...store, ...usePreferences(), ...useSession(context), theme }
}
