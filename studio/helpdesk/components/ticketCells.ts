// Cell renderers for the KB portal's ticket list, ported one-for-one from the
// agent portal's `desk/src/pages/ticket/Tickets.vue` (`columnConfig` + `listCell`)
// so both list views draw a ticket the same way. The desk components they mirror
// (IndicatorIcon, TicketPriority, StarRating, MultipleAvatar) live under `@/` in
// the desk SPA, which the Studio build cannot resolve — hence the local ports.
import { Avatar, Badge, Tooltip, call, createListResource, dayjs } from 'frappe-ui'
import { h, reactive } from 'vue'

// Status colour and portal-facing label come from HD Ticket Status, exactly as
// `useTicketStatusStore` supplies them to the agent list.
const statuses = createListResource({
  doctype: 'HD Ticket Status',
  cache: ['HD Ticket Status', 'list'],
  fields: ['label_agent', 'label_customer', 'different_view', 'category', 'color'],
  orderBy: '`tabHD Ticket Status`.order',
  pageLength: 1000,
})

function getStatus(label: string) {
  return (statuses.data || []).find(
    (status: any) => status.label_agent === label || status.label_customer === label,
  )
}

// `parseColor` from the desk store, as espresso tokens rather than its
// `!text-<color>-500` classes: those are Tailwind utilities nothing else in the
// bundle uses, and this app sits outside the bench's content globs — so every
// status drew in the inherited ink instead of its own colour.
const INK_COLORS = [
  'amber', 'blue', 'cyan', 'gray', 'green', 'orange',
  'pink', 'purple', 'red', 'teal', 'violet', 'yellow',
]

function statusColor(color: string) {
  const name = (color || 'gray').toLowerCase()
  // Espresso has no black ink; the desk maps it to the darkest gray too.
  if (name === 'black') return 'var(--ink-gray-9)'
  return `var(--ink-${INK_COLORS.includes(name) ? name : 'gray'}-6)`
}

function indicator(color: string) {
  return h(
    'svg',
    {
      style: { color: statusColor(color) },
      width: 16, height: 16, viewBox: '0 0 16 16', fill: 'none',
    },
    [h('circle', { cx: 8, cy: 8, r: 3.5, fill: 'currentColor', stroke: 'currentColor', 'stroke-width': 1 })],
  )
}

export function statusCell({ item }: any) {
  const status = getStatus(item)
  return h('div', { class: 'flex w-full items-center justify-start gap-1.5' }, [
    indicator(status?.color),
    h('span', { class: 'flex-1 truncate text-base' }, status?.label_customer || item),
  ])
}

/** The same status, for anywhere that draws its own pill rather than a list cell. */
export function statusMeta(label: string) {
  const status = getStatus(label)
  return { label: status?.label_customer || label || '', color: statusColor(status?.color) }
}

// --- priority: the signal-bars icon + name from TicketPriority.vue. The level is
// the priority's own `level` field, read the way `useTicketPriorityStore` reads it,
// so a custom priority draws the bars its level says rather than falling to Medium.
const priorities = createListResource({
  doctype: 'HD Ticket Priority',
  cache: ['HD Ticket Priority', 'list'],
  fields: ['name', 'level'],
  pageLength: 1000,
})

/** Fetched when a ticket list actually mounts, not when this module loads: both read
 *  through `frappe.client.get_list`, which a signed-out visitor cannot call — and this
 *  module is bundled into every page, including the public ones. */
export function loadTicketMeta() {
  statuses.fetch()
  priorities.fetch()
}

// Who an assignee is, by user id. `_assign` carries bare ids, so without this the list
// draws an initial and a name guessed from the email — while the ticket's own thread
// shows the same agent with their real name and face.
const agents = reactive<Record<string, { name: string; image?: string }>>({})

/** Look up the assignees on a page of rows, once per agent. */
export function loadAssignees(rows: any[]) {
  const wanted = new Set<string>()
  for (const row of rows || []) {
    for (const email of parseJson(row?._assign)) {
      if (email && !(email in agents)) wanted.add(email)
    }
  }
  if (!wanted.size) return
  // Claimed before the answer lands, so a second page does not ask again.
  wanted.forEach((email) => (agents[email] = { name: guessName(email) }))
  call('helpdesk.api.session.get_agent_avatars', { agents: [...wanted] })
    .then((found) => Object.assign(agents, found || {}))
    .catch(() => {})
}

function getLevel(name: string) {
  return (priorities.data || []).find((priority: any) => priority.name === name)?.level ?? 'Medium'
}

/** Tallest bars faded per level: High is fully solid, None is empty. */
const FADED_BARS: Record<string, number> = { High: 0, Medium: 1, Low: 2, None: 3 }
const BARS = [
  { x: 0, y: 8, height: 4 },
  { x: 4, y: 4, height: 8 },
  { x: 8, y: 0, height: 12 },
]

// Fills are inline rather than `fill-ink-gray-6` classes: this app sits outside
// the bench's Tailwind content globs, and a fill utility nothing else uses never
// compiles — which drew the whole icon in transparent.
function bar(index: number, level: string) {
  const faded = FADED_BARS[level] ?? 0
  // Bars are drawn shortest-first, so the "from the top" index counts down.
  const fromTop = BARS.length - 1 - index
  const { x, y, height } = BARS[index]
  return h('rect', {
    x, y, width: 2.5, height, rx: 0.5,
    style: { fill: fromTop < faded ? 'var(--ink-gray-3)' : 'var(--ink-gray-6)' },
  })
}

function urgentIcon() {
  const glyph = { fill: 'var(--surface-gray-1)' }
  return h('svg', { class: 'h-3.5 w-3.5', viewBox: '0 0 14 14', fill: 'none' }, [
    h('rect', { width: 14, height: 14, rx: 4, style: { fill: 'var(--ink-gray-6)' } }),
    h('rect', { x: 6.25, y: 3, width: 1.5, height: 4.75, rx: 0.75, style: glyph }),
    h('circle', { cx: 7, cy: 10, r: 0.9, style: glyph }),
  ])
}

export function priorityCell({ item }: any) {
  if (!item) return null
  const level = getLevel(item)
  const icon =
    level === 'Urgent'
      ? urgentIcon()
      : h('svg', { class: 'h-3 w-3', viewBox: '0 0 10 12', fill: 'none' }, BARS.map((_, i) => bar(i, level)))
  return h('span', { class: 'flex items-center gap-2' }, [
    h('span', { class: 'flex h-3.5 w-3.5 shrink-0 items-center justify-center' }, [icon]),
    h('span', { class: 'truncate' }, item),
  ])
}

// --- SLA: subtle badges, themed the way the agent list themes them.
const badge = (label: string, theme: string) => h(Badge, { label, theme, variant: 'subtle' })
const countdown = (deadline: string) =>
  h(Tooltip, { text: dayjs(deadline).format('LLLL') }, () =>
    h(Badge, { label: shortDuration(deadline), theme: 'orange', variant: 'subtle' }),
  )

export function responseCell({ row, item }: any) {
  if (!item) return null
  if (!row.first_responded_on && dayjs(item).isBefore(new Date())) return badge('Failed', 'red')
  if (!row.first_responded_on) return countdown(item)
  return dayjs(row.first_responded_on).isBefore(item)
    ? badge('Fulfilled', 'gray')
    : badge('Failed', 'red')
}

export function resolutionCell({ row, item }: any) {
  if (getStatus(row.status)?.category === 'Paused') return badge('Paused', 'blue')
  if (row.resolution_date) {
    const fulfilled = dayjs(row.resolution_date).isBefore(dayjs(item))
    return badge(fulfilled ? 'Fulfilled' : 'Failed', fulfilled ? 'gray' : 'red')
  }
  if (!item) return null
  return dayjs(item).isBefore(dayjs()) ? badge('Failed', 'red') : countdown(item)
}

// --- the plain `listCell` types the agent list falls back to.
export function datetimeCell({ item }: any) {
  return item ? h('span', { class: 'text-base' }, dayjs(item).fromNow()) : null
}

// MultipleAvatar.vue: one assignee reads as an avatar plus a name, several stack
// into overlapping discs. Names are derived from the email rather than looked up —
// `helpdesk.api.session.get_users`, which the agent list resolves them through, is
// agent-only.
export function avatarCell({ item }: any) {
  const assignees = parseAssignees(item)
  if (!assignees.length) return null
  if (assignees.length === 1) {
    return h(Tooltip, { text: assignees[0].email }, () =>
      h('div', { class: 'flex min-w-0 items-center gap-2 text-base line-clamp-1' }, [
        h(Avatar, {
          shape: 'circle',
          size: 'sm',
          label: assignees[0].name,
          image: assignees[0].image,
        }),
        h('div', { class: 'min-w-0 truncate' }, assignees[0].name),
      ]),
    )
  }
  return h(
    'div',
    { class: 'me-1.5 flex min-w-0 items-center' },
    assignees.map((assignee) =>
      h(Tooltip, { text: assignee.email }, () =>
        h(Avatar, {
          // my-1: the ring paints outside the border box, so it adds no height — and the
          // list cell's `overflow-x-hidden` forces overflow-y to `auto`, clipping it top
          // and bottom. The margin gives the cell room to contain its own ring.
          class: 'user-avatar -mr-1.5 my-1 ring-2 ring-[var(--surface-base)] transition hover:z-20 hover:scale-110',
          shape: 'circle',
          size: 'sm',
          label: assignee.name,
          image: assignee.image,
        }),
      ),
    ),
  )
}

/** Subject carries the unread weight: bold until the reader has opened the ticket. */
export function subjectCell({ row, item }: any, reader: string) {
  const seen = parseJson(row._seen).includes(reader)
  return h('span', { class: ['truncate flex-1', !seen && 'font-semibold'] }, item)
}

export function ratingCell({ item }: any) {
  const rating = item || 0
  return h(
    'div',
    { class: 'flex w-max flex-row-reverse gap-1' },
    [1, 0.8, 0.6, 0.4, 0.2].map((step) =>
      h('svg', {
        style: { fill: step <= rating ? 'var(--ink-yellow-5)' : 'var(--ink-gray-3)' },
        height: '16px', width: '16px', viewBox: '0 0 47.94 47.94',
        innerHTML: STAR_PATH,
      }),
    ),
  )
}

export function textCell({ item }: any) {
  return h('span', { class: 'truncate flex-1' }, item ?? '')
}

// Leading cell: muted, the way the agent list renders index 0.
export function idCell({ row }: any) {
  return h('span', { class: 'truncate text-base text-ink-gray-6' }, row.name)
}

/** `formatFullName` from the desk's user store: the local part, capitalised. */
function parseAssignees(raw: string) {
  return parseJson(raw).map((email: string) => ({
    email,
    name: agents[email]?.name || guessName(email),
    image: agents[email]?.image,
  }))
}

/** Until the lookup answers: the local part, capitalised. */
function guessName(email: string) {
  return capitalize(String(email).split('@')[0])
}

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1)
}

function parseJson(raw: string): any[] {
  try {
    const parsed = JSON.parse(raw || '[]')
    return Array.isArray(parsed) ? parsed : []
  } catch (error) {
    return []
  }
}

/** `shortDuration` from desk/src/utils.ts — compact, direction-agnostic. */
const MINUTE = 60
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

function shortDuration(target: string) {
  const seconds = Math.abs(dayjs(target).diff(dayjs(), 'second'))
  if (seconds >= DAY) {
    const days = Math.floor(seconds / DAY)
    const hours = Math.floor((seconds % DAY) / HOUR)
    const label = `${days} ${days === 1 ? 'day' : 'days'}`
    return hours ? `${label} ${hours}h` : label
  }
  if (seconds >= HOUR) {
    const hours = Math.floor(seconds / HOUR)
    const minutes = Math.floor((seconds % HOUR) / MINUTE)
    return minutes ? `${hours}h ${minutes}m` : `${hours}h`
  }
  return `${Math.floor(seconds / MINUTE)}m`
}

const STAR_PATH = `<path d="M26.285,2.486l5.407,10.956c0.376,0.762,1.103,1.29,1.944,1.412l12.091,1.757
  c2.118,0.308,2.963,2.91,1.431,4.403l-8.749,8.528c-0.608,0.593-0.886,1.448-0.742,2.285l2.065,12.042
  c0.362,2.109-1.852,3.717-3.746,2.722l-10.814-5.685c-0.752-0.395-1.651-0.395-2.403,0l-10.814,5.685
  c-1.894,0.996-4.108-0.613-3.746-2.722l2.065-12.042c0.144-0.837-0.134-1.692-0.742-2.285l-8.749-8.528
  c-1.532-1.494-0.687-4.096,1.431-4.403l12.091-1.757c0.841-0.122,1.568-0.65,1.944-1.412l5.407-10.956
  C22.602,0.567,25.338,0.567,26.285,2.486z"/>`
