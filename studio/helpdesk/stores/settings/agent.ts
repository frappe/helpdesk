import { computed } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { useSession } from '@app/stores/session'

const AGENT_SETTINGS_URL = '/helpdesk/tickets'

// Mirrors desk/src/components/Settings/settingsModal.ts: same groups, order and role checks.
// `tab` stays English; the desk matches it against its own translated labels.
function deskSettings() {
  return [
    {
      label: __('Email Settings'),
      items: [
        { tab: 'Email Accounts', label: __('Email Accounts'), icon: 'lucide-mail', access: 'staff' },
        { tab: 'Email Notifications', label: __('Email Notifications'), icon: 'lucide-mail-open', access: 'staff' },
      ],
    },
    {
      label: __('App Settings'),
      items: [
        { tab: 'General', label: __('General'), icon: 'lucide-settings', access: 'admin' },
        { tab: 'Knowledge Base', label: __('Knowledge Base'), icon: 'lucide-book-open', access: 'staff' },
        { tab: 'Portal permissions', label: __('Portal permissions'), icon: 'lucide-user-cog', access: 'staff' },
        { tab: 'Agents', label: __('Agents'), icon: 'lucide-user', access: 'staff' },
        { tab: 'Invite Agents', label: __('Invite Agents'), icon: 'lucide-user-plus', access: 'staff' },
        { tab: 'Teams', label: __('Teams'), icon: 'lucide-users', access: 'staff' },
        { tab: 'SLA Policies', label: __('SLA Policies'), icon: 'lucide-shield-check', access: 'staff' },
        { tab: 'Business Holidays', label: __('Business Holidays'), icon: 'lucide-briefcase', access: 'staff' },
        { tab: 'Assignment Rules', label: __('Assignment Rules'), icon: 'lucide-settings-2', access: 'staff' },
        { tab: 'Field Dependencies', label: __('Field Dependencies'), icon: 'lucide-git-fork', access: 'staff' },
        { tab: 'Saved Replies', label: __('Saved Replies'), icon: 'lucide-zap', access: 'agent' },
      ],
    },
    {
      label: __('Integrations'),
      items: [
        { tab: 'Telephony', label: __('Telephony'), icon: 'lucide-phone', access: 'agent' },
        { tab: 'ERPNext', label: __('ERPNext'), icon: 'lucide-blocks', access: 'staff' },
      ],
    },
  ]
}

export function createAgentSettings() {
  const session = useSession()

  const agentSettingsGroups = computed(() => {
    if (!session.isAgent.value) return []
    const isStaff = session.isAdmin.value || session.isManager.value
    const allowed = { agent: true, staff: isStaff, admin: session.isAdmin.value }
    return deskSettings()
      .map((group) => ({
        label: group.label,
        links: group.items
          .filter((item) => allowed[item.access])
          .map((item) => ({
            label: item.label,
            icon: item.icon,
            href: `${AGENT_SETTINGS_URL}?settings=${encodeURIComponent(item.tab)}`,
          })),
      }))
      .filter((group) => group.links.length)
  })

  return { agentSettingsGroups }
}
