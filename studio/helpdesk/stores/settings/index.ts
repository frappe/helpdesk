import { computed } from 'vue'
import { useColorScheme } from 'frappe-ui'
import { __, fetchTranslations } from '@helpdesk/shared/translation'
import { ROUTES } from '@app/routes'
import { usePreferences } from '@app/stores/preferences'
import { bindRouter, navigateTo } from '@app/stores/router'
import { useSession } from '@app/stores/session'
import { createAgentSettings } from './agent'
import { createSettingsCore, createSettingsDialog } from './core'
import { createOrganizationSettings } from './organization'
import { createProfileSettings } from './profile'

const AGENT_PORTAL_ROOT = '/helpdesk'

fetchTranslations()

// One instance for the whole app, or each page's copy would go stale on the others.
const core = createSettingsCore()
const organization = createOrganizationSettings(core)
const profile = createProfileSettings(core)
const agentSettings = createAgentSettings()
const dialog = createSettingsDialog(core, organization)
const session = useSession()

// Here, not in the dialog, so the saved theme applies on load rather than on open.
const { colorScheme, setColorScheme } = useColorScheme()

const theme = computed({
  get: () => colorScheme.value,
  set: setColorScheme,
})

const themeOptions = computed(() => [
  { label: __('Light'), value: 'light' },
  { label: __('Dark'), value: 'dark' },
  { label: __('System'), value: 'system' },
])

const words = computed(() => ({ raiseTicket: __('Raise a ticket') }))

const accountMenuOptions = computed(() =>
  session.isGuest.value
    ? []
    : [
        { icon: 'lucide-inbox', label: __('My tickets'), onClick: () => navigateTo(ROUTES.ticketList) },
        { icon: 'lucide-book-open', label: __('Knowledge base'), onClick: () => navigateTo(ROUTES.home) },
        { icon: 'lucide-user', label: __('My account'), onClick: () => dialog.openSettings('profile') },
        {
          icon: 'lucide-headphones',
          label: __('Agent portal'),
          condition: () => session.isAgent.value,
          onClick: () => (window.location.href = AGENT_PORTAL_ROOT),
        },
        { icon: 'lucide-log-out', label: __('Log out'), onClick: session.signOut },
      ],
)

const store = {
  words,
  themeOptions,
  theme,
  // Blocks bind `t`, not `__`.
  t: __,
  accountMenuOptions,
  isSettingsOpen: core.isSettingsOpen,
  settingsTab: core.settingsTab,
  isSettingsBusy: core.isSettingsBusy,
  settingsUser: core.settingsUser,
  organizations: core.organizations,
  loadSettings: core.loadSettings,
  confirmAction: core.confirmAction,
  isConfirmOpen: core.isConfirmOpen,
  askConfirm: core.askConfirm,
  cancelConfirm: core.cancelConfirm,
  acceptConfirm: core.acceptConfirm,
  ...organization,
  ...profile,
  ...agentSettings,
}

export function useSettingsModal(context) {
  bindRouter(context?.router)
  dialog.watchRoute()
  return { ...store, ...usePreferences(), ...session }
}
