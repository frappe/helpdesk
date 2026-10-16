import { computed } from 'vue'
import { useStorage } from '@vueuse/core'
import { useColorScheme } from 'frappe-ui'
import { __, fetchTranslations } from '@helpdesk/shared/translation'
import { ROUTES } from '@helpdesk/shared/portalRoutes'
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
const session = useSession()
const dialog = createSettingsDialog(core, organization, session)

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

// In the browser, not on the User doc: it describes this screen on this device.
export const conversationLayout = useStorage('kb:conversation-layout', 'timeline')

const conversationLayoutOptions = computed(() => [
  { label: __('Timeline'), value: 'timeline' },
  { label: __('Chat'), value: 'chat' },
])

export const accountMenuOptions = computed(() =>
  session.isGuest.value
    ? []
    : [
        { icon: 'lucide-ticket', label: __('My tickets'), onClick: () => navigateTo(ROUTES.ticketList) },
        {
          icon: 'lucide-headphones',
          label: __('Agent portal'),
          condition: () => session.isAgent.value,
          onClick: () => (window.location.href = AGENT_PORTAL_ROOT),
        },
        { icon: 'lucide-settings', label: __('Settings'), onClick: () => dialog.openSettings('profile') },
        { icon: 'lucide-log-out', label: __('Log out'), onClick: session.signOut },
      ],
)

const store = {
  themeOptions,
  theme,
  conversationLayout,
  conversationLayoutOptions,
  // Blocks bind `t`, not `__`.
  t: __,
  // Blocks bind `routes.*`, not hand-written paths.
  routes: ROUTES,
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
  session.reloadOnSettingsUpdate(context?.socket)
  dialog.watchRoute()
  return { ...store, ...session }
}
