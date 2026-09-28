import { computed } from 'vue'
import { useColorScheme } from 'frappe-ui'
import { usePreferences } from '@app/stores/preferences'
import { useSession } from '@app/stores/session'
import { __, fetchTranslations } from '@helpdesk/shared/translation'
import { createSettingsCore, createSettingsDialog } from './core'
import { createOrganizationSettings } from './organization'
import { createProfileSettings } from './profile'

fetchTranslations()

// One instance for the whole app: a private copy per page would go stale on the others.
const core = createSettingsCore()
const organization = createOrganizationSettings(core)
const profile = createProfileSettings(core)
const dialog = createSettingsDialog(core, organization)

// Here, not in the dialog, so the saved theme applies on load rather than on open.
const { colorScheme, setColorScheme } = useColorScheme()

// Writable so the theme Select can bind two-way; frappe-ui persists the choice.
const theme = computed({
  get: () => colorScheme.value,
  set: setColorScheme,
})

const themeOptions = computed(() => [
  { label: __('Light'), value: 'light' },
  { label: __('Dark'), value: 'dark' },
  { label: __('System'), value: 'system' },
])

// Here rather than on a page, because the header these words fill is shared.
const words = computed(() => ({
  raiseTicket: __('Raise a ticket'),
  status: __('Status'),
  composerPrompt: __('Type a message'),
  solveAsk: __('Did this solve your issue?'),
  solveYes: __("Yes, it's fixed"),
  solveNo: __('No, still an issue'),
  feedbackTitle: __('Feedback Rating'),
  popularHelp: __('Popular help'),
  relatedHelp: __('Related help'),
}))

const store = {
  words,
  themeOptions,
  theme,
  // The blocks bind `t`; the alias keeps them off the module's own name.
  t: __,
  isSettingsOpen: core.isSettingsOpen,
  settingsTab: core.settingsTab,
  isSettingsBusy: core.isSettingsBusy,
  settingsUser: core.settingsUser,
  organizations: core.organizations,
  // Pages that show organizations outside the dialog have to ask for them.
  loadSettings: core.loadSettings,
  confirmAction: core.confirmAction,
  isConfirmOpen: core.isConfirmOpen,
  askConfirm: core.askConfirm,
  cancelConfirm: core.cancelConfirm,
  acceptConfirm: core.acceptConfirm,
  ...organization,
  ...profile,
  ...dialog,
}

// Every page script goes through here, so the session store rides along.
export function useSettingsModal(context) {
  if (context) store.bindRouter(context.router)
  return { ...store, ...usePreferences(), ...useSession(context), theme }
}
