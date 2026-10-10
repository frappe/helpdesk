// Portal list cells; the priority and SLA pieces are the desk's, from `@helpdesk/shared`.
import { h } from 'vue'
import { Rating } from 'frappe-ui'
import { PriorityIcon, resolutionBadge, responseBadge } from '@helpdesk/shared/ticketCells'
import { timeAgo } from '@helpdesk/shared/utils'
import { getPriorityLevel, getStatus, statusMeta } from '@app/stores/ticketMeta'
import { parseJson } from '@app/utils'
import PortalStatusPill from '@app/components/ticket/PortalStatusPill.vue'

export function statusCell({ item }: any) {
  return h(PortalStatusPill, { ...statusMeta(item), size: 'sm', class: 'w-full' })
}

export function priorityCell({ item }: any) {
  if (!item) return null
  return h('span', { class: 'flex items-center gap-2' }, [
    h('span', { class: 'flex h-3.5 w-3.5 shrink-0 items-center justify-center' }, [
      h(PriorityIcon, { level: getPriorityLevel(item) }),
    ]),
    h('span', { class: 'truncate' }, item),
  ])
}

export function responseCell({ row, item }: any) {
  return responseBadge(row, item)
}

export function resolutionCell({ row, item }: any) {
  return resolutionBadge(row, item, getStatus(row.status)?.category === 'Paused')
}

export function datetimeCell({ item }: any) {
  return item ? h('span', { class: 'text-base' }, timeAgo(item)) : null
}

export function subjectCell({ row, item }: any, reader: string) {
  const seen = parseJson(row._seen, []).includes(reader)
  return h('span', { class: ['truncate flex-1', !seen && 'font-semibold'] }, item)
}

// HD Ticket stores the rating as a fraction of five stars.
export function ratingCell({ item }: any) {
  return h(Rating, { modelValue: (item || 0) * 5, disabled: true, size: 'sm' })
}

export function textCell({ item }: any) {
  return h('span', { class: 'truncate flex-1' }, item ?? '')
}

export function idCell({ row }: any) {
  return h('span', { class: 'truncate text-base text-ink-gray-6' }, row.name)
}
