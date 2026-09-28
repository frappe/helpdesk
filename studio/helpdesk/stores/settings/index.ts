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

// The desk SPA's root, the mirror of its own CUSTOMER_PORTAL_ROOT.
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

// The header these words fill is shared by every page.
const words = computed(() => ({ raiseTicket: __('Raise a ticket') }))

// A guest has no tickets, account or session to offer.
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
                // A hard navigation: the desk is a separate SPA, not a route here.
                onClick: () => (window.location.href = AGENT_PORTAL_ROOT),
              },
            ]
          : []),
        { icon: 'lucide-log-out', label: __('Log out'), onClick: session.signOut },
      ],
)

const store = {
  words,
  themeOptions,
  theme,
  // The blocks bind `t`; the alias keeps them off the module's own name.
  t: __,
  accountMenuOptions,
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
}

// Every page script goes through here, so the session store rides along.
export function useSettingsModal(context) {
  bindRouter(context?.router)
  dialog.watchRoute()
  return { ...store, ...usePreferences(), ...session }
}
