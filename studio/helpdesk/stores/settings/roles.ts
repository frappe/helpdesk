import LucideBriefcase from '~icons/lucide/briefcase'
import LucideCrown from '~icons/lucide/crown'
import LucideUser from '~icons/lucide/user'
import { __ } from '@helpdesk/shared/translation'

export const ROLES = {
  Owner: { icon: LucideCrown, theme: 'blue' },
  Manager: { icon: LucideBriefcase, theme: 'green' },
  Member: { icon: LucideUser, theme: 'gray' },
} as const

export type RoleLabel = keyof typeof ROLES

export const ASSIGNABLE_ROLES: RoleLabel[] = ['Manager', 'Member']

export function roleLabel(role: RoleLabel) {
  return { Owner: __('Owner'), Manager: __('Manager'), Member: __('Member') }[role]
}
