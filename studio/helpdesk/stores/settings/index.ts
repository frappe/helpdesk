import { computed } from 'vue'
import { useColorScheme } from 'frappe-ui'
import { __, fetchTranslations } from '@helpdesk/shared/translation'
import { ROUTES } from '@app/routes'
import { usePreferences } from '@app/stores/preferences'
import { bindRouter, navigateTo } from '@app/stores/router'
import { useSession } from '@app/stores/session'
import { createSettingsCore, createSettingsDialog } from './core'
import { createOrganizationSettings } from './organization'
import { createProfileSettings } from './profile'

const AGENT_PORTAL_ROOT = '/helpdesk'

fetchTranslations()

// One instance for the whole app: a private copy per page would go stale on the others.
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

const accountMenuOptions = computed(() =>
  session.isGuest.value
    ? [{ icon: 'lucide-log-in', label: __('Log in'), onClick: session.signIn }]
    : [
        { icon: 'lucide-inbox', label: __('My tickets'), onClick: () => navigateTo(ROUTES.ticketList) },
        { icon: 'lucide-user', label: __('My account'), onClick: () => dialog.openSettings('profile') },
        ...(session.isAgent.value
          ? [
              {
                icon: 'lucide-headphones',
                label: __('Agent portal'),
                onClick: () => (window.location.href = AGENT_PORTAL_ROOT),
              },
            ]
          : []),
        { icon: 'lucide-log-out', label: __('Log out'), onClick: session.signOut },
      ],
)

const store = {
  themeOptions,
  theme,
  // The blocks bind `t`; the alias keeps them off the module's own name.
  t: __,
  accountMenuOptions,
  // HD Form Script header actions; the ticket pages fill them.
  customActions: [],
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
  return { ...store, ...usePreferences(), ...session }
}
