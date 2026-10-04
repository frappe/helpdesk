import { computed } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { useSession } from '@app/stores/session'

const AGENT_SETTINGS_URL = '/helpdesk/tickets'

// Mirrors desk/src/components/Settings/settingsModal.ts, whose literal `__()` calls extract these labels.
const DESK_SETTINGS = [
  {
    group: 'Email Settings',
    items: [
      { tab: 'Email Accounts', icon: 'lucide-mail', access: 'staff' },
      { tab: 'Email Notifications', icon: 'lucide-mail-open', access: 'staff' },
    ],
  },
  {
    group: 'App Settings',
    items: [
      { tab: 'General', icon: 'lucide-settings', access: 'admin' },
      { tab: 'Knowledge Base', icon: 'lucide-book-open', access: 'staff' },
      { tab: 'Portal permissions', icon: 'lucide-user-cog', access: 'staff' },
      { tab: 'Agents', icon: 'lucide-user', access: 'staff' },
      { tab: 'Invite Agents', icon: 'lucide-user-plus', access: 'staff' },
      { tab: 'Teams', icon: 'lucide-users', access: 'staff' },
      { tab: 'SLA Policies', icon: 'lucide-shield-check', access: 'staff' },
      { tab: 'Business Holidays', icon: 'lucide-briefcase', access: 'staff' },
      { tab: 'Assignment Rules', icon: 'lucide-settings-2', access: 'staff' },
      { tab: 'Field Dependencies', icon: 'lucide-git-fork', access: 'staff' },
      { tab: 'Saved Replies', icon: 'lucide-zap', access: 'agent' },
    ],
  },
  {
    group: 'Integrations',
    items: [
      { tab: 'Telephony', icon: 'lucide-phone', access: 'agent' },
      { tab: 'ERPNext', icon: 'lucide-blocks', access: 'staff' },
    ],
  },
]

export function createAgentSettings() {
  const session = useSession()

  const agentSettingsGroups = computed(() => {
    if (!session.isAgent.value) return []
    const isStaff = session.isAdmin.value || session.isManager.value
    const allowed = { agent: true, staff: isStaff, admin: session.isAdmin.value }
    return DESK_SETTINGS.map((group) => ({
      label: __(group.group),
      links: group.items
        .filter((item) => allowed[item.access])
        .map((item) => ({
          label: __(item.tab),
          icon: item.icon,
          href: `${AGENT_SETTINGS_URL}?settings=${encodeURIComponent(item.tab)}`,
        })),
    })).filter((group) => group.links.length)
  })

  return { agentSettingsGroups }
}
