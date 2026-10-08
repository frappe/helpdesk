// Ported from the desk's list cells, which Studio cannot import (they live under `@/`).
import { h } from 'vue'
import { Badge, Rating, Tooltip, dayjsLocal } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { shortDuration, timeAgo } from '@helpdesk/shared/utils'
import { STATUS_DOT_CLASSES, getPriorityLevel, getStatus, statusMeta } from '@app/stores/ticketMeta'
import { parseJson } from '@app/utils'

export function statusCell({ item }: any) {
  const status = statusMeta(item)
  return h('div', { class: 'flex w-full items-center justify-start gap-1.5' }, [
    h('span', { class: ['size-[7px] shrink-0 rounded-full', STATUS_DOT_CLASSES[status.color]] }),
    h('span', { class: 'flex-1 truncate text-base' }, status.label),
  ])
}

const FADED_BARS: Record<string, number> = { High: 0, Medium: 1, Low: 2, None: 3 }
const BARS = [
  { x: 0, y: 8, height: 4 },
  { x: 4, y: 4, height: 8 },
  { x: 8, y: 0, height: 12 },
]

function bar(index: number, level: string) {
  const faded = FADED_BARS[level] ?? 0
  // Bars are drawn shortest-first, so the "from the top" index counts down.
  const fromTop = BARS.length - 1 - index
  const { x, y, height } = BARS[index]
  return h('rect', {
    x, y, width: 2.5, height, rx: 0.5,
    class: fromTop < faded ? 'fill-ink-gray-3' : 'fill-ink-gray-6',
  })
}

function urgentIcon() {
  const glyph = 'fill-[var(--surface-gray-1)]'
  return h('svg', { class: 'size-3.5', viewBox: '0 0 14 14', fill: 'none' }, [
    h('rect', { width: 14, height: 14, rx: 4, class: 'fill-ink-gray-6' }),
    h('rect', { x: 6.25, y: 3, width: 1.5, height: 4.75, rx: 0.75, class: glyph }),
    h('circle', { cx: 7, cy: 10, r: 0.9, class: glyph }),
  ])
}

export function priorityCell({ item }: any) {
  if (!item) return null
  const level = getPriorityLevel(item)
  const icon =
    level === 'Urgent'
      ? urgentIcon()
      : h('svg', { class: 'h-3 w-3', viewBox: '0 0 10 12', fill: 'none' }, BARS.map((_, i) => bar(i, level)))
  return h('span', { class: 'flex items-center gap-2' }, [
    h('span', { class: 'flex h-3.5 w-3.5 shrink-0 items-center justify-center' }, [icon]),
    h('span', { class: 'truncate' }, item),
  ])
}

function badge(label: string, theme: string) {
  return h(Badge, { label, theme, variant: 'subtle' })
}

function slaBadge(metOn: string | undefined, due: string) {
  if (metOn) {
    return dayjsLocal(metOn).isBefore(dayjsLocal(due)) ? badge(__('Fulfilled'), 'gray') : badge(__('Failed'), 'red')
  }
  if (dayjsLocal(due).isBefore(dayjsLocal())) return badge(__('Failed'), 'red')
  return h(Tooltip, { text: dayjsLocal(due).format('LLLL') }, () => badge(shortDuration(due), 'amber'))
}

export function responseCell({ row, item }: any) {
  if (!item) return null
  return slaBadge(row.first_responded_on, item)
}

export function resolutionCell({ row, item }: any) {
  if (getStatus(row.status)?.category === 'Paused') return badge(__('Paused'), 'blue')
  if (!item && !row.resolution_date) return null
  return slaBadge(row.resolution_date, item)
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
