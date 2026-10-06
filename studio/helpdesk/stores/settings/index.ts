import { computed } from 'vue'
import { useColorScheme } from 'frappe-ui'
import { __, fetchTranslations } from '@helpdesk/shared/translation'
import { ROUTES } from '@app/routes'
import { bindRouter, navigateTo } from '@app/stores/router'
import { useSession } from '@app/stores/session'
import { createSettingsCore, createSettingsDialog } from './core'
import { createOrganizationSettings } from './organization'
import { createProfileSettings } from './profile'

const AGENT_PORTAL_ROOT = '/helpdesk'

fetchTranslations()

// One instance for the whole app, or each page's copy would go stale on the others.
const core = createSettingsCore()
const organization = createOrganizationSettings(core)
const profile = createProfileSettings(core)
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

export const accountMenuOptions = computed(() =>
  session.isGuest.value
    ? []
    : [
        { icon: 'lucide-ticket', label: __('My tickets'), onClick: () => navigateTo(ROUTES.ticketList) },
        { icon: 'lucide-settings', label: __('Settings'), onClick: () => dialog.openSettings('profile') },
        {
          icon: 'lucide-arrow-left-right',
          label: __('Agent portal'),
          condition: () => session.isAgent.value,
          onClick: () => (window.location.href = AGENT_PORTAL_ROOT),
        },
        { icon: 'lucide-log-out', label: __('Log out'), onClick: session.signOut },
      ],
)

const store = {
  themeOptions,
  theme,
  // Blocks bind `t`, not `__`.
  t: __,
  accountMenuOptions,
  // HD Form Script header actions; the ticket pages fill them.
  customActions: [],
  // The admin's header links; the knowledge base pages fill them.
  headerLinks: [],
  isSettingsOpen: core.isSettingsOpen,
  settingsTab: core.settingsTab,
  isSettingsBusy: core.isSettingsBusy,
  settingsUser: core.settingsUser,
  organizations: core.organizations,
  loadSettings: core.loadSettings,
  ...organization,
  ...profile,
}

export function useSettingsModal(context) {
  bindRouter(context?.router)
  dialog.watchRoute()
  return { ...store, ...session }
}
