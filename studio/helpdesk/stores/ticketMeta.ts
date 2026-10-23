import { createListResource } from 'frappe-ui'

// "Resolved" and "Closed" share this category; only the name differs.
const RESOLVED_CATEGORY = 'Resolved'
export const CLOSED_STATUS = 'Closed'

const statuses = createListResource({
  doctype: 'HD Ticket Status',
  cache: ['portal', 'HD Ticket Status'],
  fields: ['label_agent', 'label_customer', 'different_view', 'category', 'color'],
  orderBy: '`tabHD Ticket Status`.order',
  pageLength: 1000,
})

const priorities = createListResource({
  doctype: 'HD Ticket Priority',
  cache: ['portal', 'HD Ticket Priority'],
  fields: ['name', 'level', 'description'],
  pageLength: 1000,
})

// Not at import: guests cannot call `frappe.client.get_list`.
function fetchOnce(resource) {
  if (!resource.list.fetched && !resource.list.loading) resource.fetch()
}

export function loadStatuses() {
  fetchOnce(statuses)
}

export function loadPriorities() {
  fetchOnce(priorities)
}

export function loadTicketMeta() {
  loadStatuses()
  loadPriorities()
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

// As the desk: customer label only while `different_view` is on.
export function statusMeta(label: string) {
  const status = getStatus(label)
  const shown = status?.different_view ? status.label_customer : status?.label_agent
  return { label: shown || label || '', color: status?.color }
}

export function getPriority(name: string) {
  return (priorities.data || []).find((priority: any) => priority.name === name)
}

export function getPriorityLevel(name: string) {
  return getPriority(name)?.level ?? 'Medium'
}
