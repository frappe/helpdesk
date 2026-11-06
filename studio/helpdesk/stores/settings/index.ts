import { computed } from 'vue'
import { useColorScheme } from 'frappe-ui'
import { __, fetchTranslations } from '@helpdesk/shared/translation'
import { ROUTES } from '@helpdesk/shared/portalRoutes'
import { bindRouter, navigateTo } from '@app/stores/router'
import { askConfirm } from '@helpdesk/shared/utils'
import { useSession } from '@app/stores/session'
import { knowledgeBaseDraft } from '@helpdesk/shared/settings/knowledgeBaseDraft.ts'
import { createSettingsCore, createSettingsDialog } from './core'
import { createOrganizationSettings } from './organization'
import { createProfileSettings } from './profile'
import { conversationLayout } from '@app/stores/conversationLayout'

const AGENT_PORTAL_ROOT = '/helpdesk'

fetchTranslations()

// One shared instance, or each page's copy goes stale.
const core = createSettingsCore()
const organization = createOrganizationSettings(core)
const profile = createProfileSettings(core)
const session = useSession()
const dialog = createSettingsDialog(core, organization, session)

// Here, so the saved theme applies on load, not on dialog open.
const { colorScheme, setColorScheme, resolvedColorScheme, toggleColorScheme } = useColorScheme()

const theme = computed({
  get: () => colorScheme.value,
  set: setColorScheme,
})

export const themeIcon = computed(() => (resolvedColorScheme.value === 'dark' ? 'lucide-sun' : 'lucide-moon-star'))
export const toggleTheme = toggleColorScheme

const themeOptions = computed(() => [
  { label: __('Light'), value: 'light' },
  { label: __('Dark'), value: 'dark' },
  { label: __('System'), value: 'system' },
])

export { conversationLayout }

const conversationLayoutOptions = computed(() => [
  { label: __('Timeline'), value: 'timeline', icon: 'lucide-list' },
  { label: __('Chat'), value: 'chat', icon: 'lucide-messages-square' },
])

// Leaving a dirty Knowledge Base tab asks first, as the desk does.
const settingsTab = computed({
  get: () => core.settingsTab.value,
  set: (tab) => {
    if (tab === core.settingsTab.value) return
    const draft = knowledgeBaseDraft.value
    if (!draft?.isDirty.value) {
      core.settingsTab.value = tab
      return
    }
    askConfirm({
      title: __('Unsaved changes'),
      message: __('Are you sure you want to change tabs? Unsaved changes will be lost.'),
      label: __('Confirm'),
      action: () => {
        draft.discard()
        core.settingsTab.value = tab
      },
    })
  },
})

// Stays open while the Knowledge Base tab is dirty, as the desk does.
const isSettingsOpen = computed({
  get: () => core.isSettingsOpen.value,
  set: (open) => {
    if (open || !knowledgeBaseDraft.value?.isDirty.value) core.isSettingsOpen.value = open
  },
})

const knowledgeBase = {
  knowledgeBaseIsDirty: computed(() => Boolean(knowledgeBaseDraft.value?.isDirty.value)),
  knowledgeBaseSaving: computed(() => Boolean(knowledgeBaseDraft.value?.saving.value)),
  previewKnowledgeBase: () => knowledgeBaseDraft.value?.preview(),
  saveKnowledgeBase: async () => {
    if (await knowledgeBaseDraft.value?.save()) session.reloadSession()
  },
}

export const accountMenuOptions = computed(() =>
  session.isGuest.value
    ? []
    : [
        { icon: 'lucide-home', label: __('Home'), onClick: () => navigateTo(ROUTES.home) },
        { icon: 'lucide-ticket', label: __('My tickets'), onClick: () => navigateTo(ROUTES.ticketList) },
        {
          icon: 'lucide-headphones',
          label: __('Agent portal'),
          condition: () => session.isAgent.value,
          onClick: () => (window.location.href = AGENT_PORTAL_ROOT),
        },
        {
          icon: 'lucide-settings',
          label: __('Settings'),
          // As in the desk: the settings dialog is desktop-only.
          condition: () => !session.isPhone.value,
          onClick: () => dialog.openSettings('profile'),
        },
        { icon: themeIcon.value, label: __('Toggle theme'), onClick: toggleTheme },
        {
          group: __('Log out'),
          hideLabel: true,
          options: [{ icon: 'lucide-log-out', label: __('Log out'), onClick: session.signOut }],
        },
      ],
)

const store = {
  themeOptions,
  theme,
  conversationLayout,
  conversationLayoutOptions,
  t: __,
  routes: ROUTES,
  accountMenuOptions,
  // Placeholders the pages override.
  showLogin: session.isGuest,
  customActions: [],
  headerLinks: [],
  themeIcon: '',
  isSettingsOpen,
  settingsTab,
  isSettingsBusy: core.isSettingsBusy,
  settingsUser: core.settingsUser,
  organizations: core.organizations,
  settingsLoaded: core.settingsLoaded,
  loadSettings: core.loadSettings,
  ensureSettings: core.ensureSettings,
  ...organization,
  ...profile,
  ...knowledgeBase,
}

export function useSettingsModal(context) {
  bindRouter(context?.router)
  session.reloadOnSettingsUpdate(context?.socket)
  dialog.watchRoute()
  return { ...store, ...session }
}
