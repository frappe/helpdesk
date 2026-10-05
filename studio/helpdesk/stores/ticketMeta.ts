import { createListResource } from 'frappe-ui'

// "Resolved" and "Closed" share this category; only the name tells them apart.
const RESOLVED_CATEGORY = 'Resolved'
export const CLOSED_STATUS = 'Closed'

// Full literals: Tailwind's scanner cannot see classes built from data.
export const STATUS_DOT_CLASSES = {
  amber: 'bg-[var(--ink-amber-6)]',
  blue: 'bg-[var(--ink-blue-6)]',
  cyan: 'bg-[var(--ink-cyan-6)]',
  gray: 'bg-[var(--ink-gray-6)]',
  green: 'bg-[var(--ink-green-6)]',
  orange: 'bg-[var(--ink-orange-6)]',
  pink: 'bg-[var(--ink-pink-6)]',
  purple: 'bg-[var(--ink-purple-6)]',
  red: 'bg-[var(--ink-red-6)]',
  teal: 'bg-[var(--ink-teal-6)]',
  violet: 'bg-[var(--ink-violet-6)]',
  yellow: 'bg-[var(--ink-yellow-6)]',
  black: 'bg-[var(--ink-gray-9)]',
}

export type StatusColor = keyof typeof STATUS_DOT_CLASSES

const statuses = createListResource({
  doctype: 'HD Ticket Status',
  cache: ['HD Ticket Status', 'list'],
  fields: ['label_agent', 'label_customer', 'different_view', 'category', 'color'],
  orderBy: '`tabHD Ticket Status`.order',
  pageLength: 1000,
})

const priorities = createListResource({
  doctype: 'HD Ticket Priority',
  cache: ['HD Ticket Priority', 'list'],
  fields: ['name', 'level', 'description'],
  pageLength: 1000,
})

// Not at import: a signed-out visitor cannot call `frappe.client.get_list`.
export function loadTicketMeta() {
  statuses.fetch()
  priorities.fetch()
}

export function getStatus(label: string) {
  return (statuses.data || []).find(
    (status: any) => status.label_agent === label || status.label_customer === label,
  )
}

export function isClosedStatus(label: string) {
  return label === CLOSED_STATUS
}

export function isResolvedStatus(label: string) {
  return !isClosedStatus(label) && getStatus(label)?.category === RESOLVED_CATEGORY
}

export function statusMeta(label: string) {
  const status = getStatus(label)
  return { label: status?.label_customer || label || '', color: statusColor(status?.color) }
}

function statusColor(color: string): StatusColor {
  const name = (color || 'gray').toLowerCase()
  return name in STATUS_DOT_CLASSES ? (name as StatusColor) : 'gray'
}

export function getPriority(name: string) {
  return (priorities.data || []).find((priority: any) => priority.name === name)
}

export function getPriorityLevel(name: string) {
  return getPriority(name)?.level ?? 'Medium'
}
