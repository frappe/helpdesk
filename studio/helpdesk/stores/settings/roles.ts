import LucideBriefcase from '~icons/lucide/briefcase'
import LucideCrown from '~icons/lucide/crown'
import LucideUser from '~icons/lucide/user'

// Owner is the primary contact, whom HD Customer keeps a manager; it holds no role of its own.
export const ROLES = {
  Owner: { icon: LucideCrown, theme: 'blue', role: 'HD Customer Manager' },
  Manager: { icon: LucideBriefcase, theme: 'green', role: 'HD Customer Manager' },
  Member: { icon: LucideUser, theme: 'gray', role: 'HD Customer' },
} as const

export type RoleLabel = keyof typeof ROLES
