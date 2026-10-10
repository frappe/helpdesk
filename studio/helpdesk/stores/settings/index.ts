import { computed } from 'vue'
import { useStorage } from '@vueuse/core'
import { useColorScheme } from 'frappe-ui'
import { __, fetchTranslations } from '@helpdesk/shared/translation'
import { ROUTES } from '@helpdesk/shared/portalRoutes'
import { bindRouter, navigateTo } from '@app/stores/router'
import { askConfirm } from '@app/utils'
import { useSession } from '@app/stores/session'
import { knowledgeBaseDraft } from '@helpdesk/shared/settings/knowledgeBaseDraft.ts'
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
const { colorScheme, setColorScheme, resolvedColorScheme, toggleColorScheme } = useColorScheme()

const theme = computed({
  get: () => colorScheme.value,
  set: setColorScheme,
})

// The header's toggle, on every page: the knowledge base scripts are not what carries it.
const themeIcon = computed(() => (resolvedColorScheme.value === 'dark' ? 'lucide-sun' : 'lucide-moon-star'))

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

// Leaving the Knowledge Base tab with unsaved changes asks first, as the desk's settings do.
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

// Like the desk's, the dialog stays open while the Knowledge Base tab has unsaved changes.
const isSettingsOpen = computed({
  get: () => core.isSettingsOpen.value,
  set: (open) => {
    if (open || !knowledgeBaseDraft.value?.isDirty.value) core.isSettingsOpen.value = open
  },
})

// The Knowledge Base panel's header buttons; the panel's form makes the draft.
const knowledgeBase = {
  knowledgeBaseIsDirty: computed(() => Boolean(knowledgeBaseDraft.value?.isDirty.value)),
  knowledgeBaseCanPreview: computed(() => Boolean(knowledgeBaseDraft.value?.canPreview.value)),
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
  // The admin's header links; the knowledge base pages fill them.
  headerLinks: [],
  themeIcon,
  toggleTheme: toggleColorScheme,
  isSettingsOpen,
  settingsTab,
  isSettingsBusy: core.isSettingsBusy,
  settingsUser: core.settingsUser,
  organizations: core.organizations,
  loadSettings: core.loadSettings,
  ...organization,
  ...profile,
  ...knowledgeBase,
}

export function useSettingsModal(context) {
  bindRouter(context?.router)
  dialog.watchRoute()
  return { ...store, ...session }
}
