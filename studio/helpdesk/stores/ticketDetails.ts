import { computed } from 'vue'
import { dayjs } from 'frappe-ui'
import { statusMeta } from '@app/components/ticketCells'
import { t, tFormat } from '@app/stores/translations'

// Everything the summary sidebar shows, finished for display — label, wording, colour —
// because the sidebar is drawn by Studio blocks that only bind.
//
// Where the agent portal's `TicketCustomerSidebar.vue` reports SLA compliance, this tells
// the same facts as a story: who has it, what is owed next, when it ended and how long that
// took. Same fields, read as progress rather than as a report card — "Failed" is not a
// useful thing to show the person still waiting.

const DATE_FORMAT = 'ddd, MMM D, YYYY h:mm A'
const STEP_FORMAT = 'ddd D MMM, h:mm a'
const DUE_FORMAT = 'ddd D MMM, h:mm a'
const CLOCK_FORMAT = 'h:mm a'
const EMPTY = '—'
// The page's own heading already carries the subject; a second copy in the sidebar is noise.
const HIDDEN_FIELDS = ['subject']
// A reply inside this window reads as "someone was already there", not as a measured wait.
const IMMEDIATE_SECONDS = 5 * 60

export function useTicketDetails(ticket, thread) {
  const data = computed(() => ticket.data || {})
  const firstReply = computed(() => thread?.firstAgentReply.value)

  // Who raised it, and where it came from. `via_customer_portal` is the only channel HD
  // Ticket records, so everything else is mail by elimination.
  const identity = computed(() => ({
    // `full_name` before the docname: a Contact is named by whatever it was created from —
    // an email local part, an import — and the person's actual name lives in the field.
    name:
      data.value.contact?.full_name ||
      data.value.contact?.name ||
      data.value.raised_by ||
      '',
    image: data.value.contact?.image || '',
    reference: data.value.name
      ? `#${data.value.name} via ${data.value.via_customer_portal ? 'Portal' : 'Email'}`
      : '',
  }))

  // Label and colour as HD Ticket Status defines them, so the pill matches the dot the
  // ticket list draws for the same ticket — and a helpdesk that recolours a status is
  // honoured without touching this app.
  const statusPill = computed(() => statusMeta(data.value.status))

  // Everything the sidebar says about the ticket itself, as one list: who is handling it
  // and how urgently first, then whatever else the ticket's template asks for. One shape
  // for all of them — a reader scanning label-and-value has no use for the distinction.
  const basics = computed(() => [
    { label: t('Team'), value: data.value.agent_group || EMPTY },
    { label: t('Priority'), value: data.value.priority || EMPTY },
    ...templateFields(),
  ])

  // An empty field keeps its row: a template field with nothing in it is still something
  // the helpdesk asked for, and a dash says so where a missing row would just look complete.
  function templateFields() {
    return (data.value.template?.fields || [])
      .filter(
        (templateField) =>
          !templateField.hide_from_customer &&
          !HIDDEN_FIELDS.includes(templateField.fieldname),
      )
      .map((templateField) => ({
        label: t(templateField.label),
        value: formatValue(templateField, data.value[templateField.fieldname]) || EMPTY,
      }))
  }

  function formatValue(templateField, value) {
    if (!value) return value
    if (templateField.fieldtype === 'Date') return dayjs(value).format('DD-MM-YYYY')
    if (templateField.fieldtype === 'Datetime') return dayjs(value).format(DATE_FORMAT)
    return value
  }

  // The milestones every ticket has. No per-message rows: the thread on the left already is
  // the messages, and repeating them here would say nothing new.
  const timeline = computed(() => {
    const steps = [received(), assigned(), answered(), ...resolution(), ...closing()]
    // The amber ring marks one thing to watch, so it goes on the frontier: the first unmet
    // milestone *past* everything already reached. Searching from the top would ring a step
    // that later ones have overtaken — a ticket can be answered without ever having been
    // formally assigned.
    let reached = -1
    steps.forEach((step, index) => {
      if (step.state === 'done' || step.state === 'closed') reached = index
    })
    const next = steps.slice(reached + 1).find((step) => step.state === 'pending')
    if (next) next.state = 'next'
    return steps
  })

  function received() {
    // The one absolute date the rail shows: "when did I raise this?" is a question a
    // customer actually asks, and nothing above it gives an answer.
    return step(t('Request received'), at(data.value.creation), 'done', data.value.creation)
  }

  // When support took it on, named where possible. No assignment timestamp is readable by a
  // customer — the ToDo behind an assignment and HD Ticket Activity are both agent-only — so
  // the first agent reply stands in: the moment support demonstrably had the ticket. That
  // makes the stamp an upper bound on the pick-up, and the closest honest one available.
  //
  // A reply counts as ownership on its own. Assignment is optional in Frappe, so a ticket an
  // agent has answered can still carry an empty `_assign` — and telling the customer nobody
  // has picked it up, directly above that agent's answer, is a lie. `_assign` alone buys only
  // a state: it carries bare user ids, no name and no time.
  function assigned() {
    const reply = firstReply.value
    if (reply)
      return step(tFormat('Assigned to', reply.sender), since(reply.creation), 'done', reply.creation)
    if (assignees().length)
      return step(t('Assigned to agent'), t('An agent is on it'), 'done')
    return step(t('Assigned to agent'), t('Waiting to be assigned'), 'pending')
  }

  function assignees() {
    try {
      return JSON.parse(data.value._assign || '[]')
    } catch {
      return []
    }
  }

  function answered() {
    const reply = firstReply.value
    if (!reply) return awaiting(t('Awaiting first response'), data.value.response_by)
    return step(t('First response'), speedOf(reply), 'done', reply.creation)
  }

  /** How the answer felt: instant, or a wait worth naming — and whether it beat the
   *  target the list is grading it against. */
  function speedOf(reply) {
    const waited = Math.max(dayjs(reply.creation).diff(dayjs(data.value.creation), 's'), 0)
    const answered =
      waited <= IMMEDIATE_SECONDS ? 'Answered immediately' : `Answered in ${duration(waited)}`
    return withLateness(
      answered,
      lateBy(reply.creation, data.value.response_by, data.value.first_response_failed_by),
    )
  }

  // The ending, and the wait for it. The wait only appears once support has answered —
  // before that the ticket is waiting on a first reply, and the step above says so.
  //
  // A ticket that ended without ever being resolved gets no resolved step at all: the close
  // below is the whole of what happened to it.
  function resolution() {
    const on = data.value.resolution_date
    if (on) return wasResolved() ? [step(t('Resolved'), resolvedAt(on), 'done', on)] : []
    if (!firstReply.value) return [step(t('Resolved'), '', 'pending')]
    return [awaiting(t('Awaiting resolution'), data.value.resolution_by)]
  }

  /** Whether anything was actually resolved, as far as a customer can tell.
   *
   *  HD Ticket stamps `resolution_date` when a ticket enters the resolved *category*, so a
   *  ticket closed outright carries one exactly like a fixed one — the date alone cannot tell
   *  "we sorted it" from "we filed it away", and reading it as the former put a green
   *  `Resolved` on tickets nobody had so much as picked up. What can tell them apart: a status
   *  that still says Resolved, or an account of the fix an agent wrote down. */
  function wasResolved() {
    return data.value.status !== 'Closed' || Boolean(data.value.resolution_details)
  }

  /** How long it took, and by how much that missed the target. */
  function resolvedAt(on: string) {
    const took = Math.max(dayjs(on).diff(dayjs(data.value.creation), 's'), 0)
    const taken = took <= IMMEDIATE_SECONDS ? 'Resolved immediately' : `Resolved in ${duration(took)}`
    return withLateness(
      taken,
      lateBy(on, data.value.resolution_by, data.value.resolution_failed_by),
    )
  }

  /** A milestone that overran its target says so. The ticket list grades the same two
   *  moments with a red "Failed" badge, so a rail that reported only the elapsed time read
   *  as a different account of the same ticket — this is that fact in the sidebar's voice. */
  function withLateness(said: string, by: number) {
    return by ? `${said} · ${duration(by)} late` : said
  }

  /** How far past its target a milestone landed, zero when it was in time. */
  function lateBy(on: string, due: string, failedBy: number) {
    // The SLA's own figure where there is one — business hours, so it agrees with the number
    // the agent portal reports, and it is written only on an actual miss.
    if (failedBy) return failedBy
    if (!due || !dayjs(on).isAfter(dayjs(due))) return 0
    return dayjs(on).diff(dayjs(due), 's')
  }

  // Closing is its own milestone, and only a closed ticket has reached it. It carries a time
  // only where that time is knowable: entering the resolved category is what stamps
  // `resolution_date`, so on a ticket closed outright that stamp *is* the close — while on one
  // resolved first it belongs to the step above, and nothing records the close itself.
  function closing() {
    if (data.value.status !== 'Closed') return []
    const on = data.value.resolution_date
    // Resolved first: that moment belongs to the step above, and nothing records the close
    // itself, so this row says only that it ended.
    return [step(t('Closed'), wasResolved() ? '' : since(on), 'closed', wasResolved() ? '' : on)]
  }

  /** A milestone still owed, worded by its target. Always `pending`, so the frontier logic
   *  gives it the amber ring: this is the step the reader is waiting on, and an overdue
   *  target is said in words rather than shouted in colour. */
  function awaiting(title: string, due: string) {
    if (!due) return step(title, t('Pending'), 'pending')
    if (dayjs().isAfter(dayjs(due))) return step(title, `Overdue by ${countdown(due)}`, 'pending')
    return step(title, `Due ${dueWording(due)}`, 'pending')
  }

  /** `at` is the moment the row is about, kept raw for the hover: the rail reads as
   *  progress, so the visible line is elapsed wording and the stamp waits under the
   *  pointer — the way the thread's own timestamps behave. */
  function step(title: string, subtitle: string, state: string, on?: string) {
    return { title, subtitle, state, fullDate: on ? dayjs(on).format(DATE_FORMAT) : '' }
  }

  /** "9 minutes later", from the moment the ticket arrived. */
  function since(on: string) {
    const elapsed = Math.max(dayjs(on).diff(dayjs(data.value.creation), 's'), 0)
    return elapsed <= IMMEDIATE_SECONDS ? 'moments later' : `${duration(elapsed)} later`
  }

  function at(value: string) {
    return value ? dayjs(value).format(STEP_FORMAT) : ''
  }

  /** A deadline as someone would say it: the clock alone while it falls today. */
  function dueWording(target: string) {
    const due = dayjs(target)
    if (due.isSame(dayjs(), 'day')) return `${due.format(CLOCK_FORMAT)} today`
    if (due.isSame(dayjs().add(1, 'day'), 'day')) return `${due.format(CLOCK_FORMAT)} tomorrow`
    return due.format(DUE_FORMAT)
  }

  /** Distance to a target, either side of it — the caller words the direction. */
  function countdown(target: string) {
    return duration(Math.abs(dayjs(target).diff(dayjs(), 's')))
  }

  // The two most significant units, as `formatSeconds` words them in the agent portal's
  // analytics: "2d 9h", "44m". Never four — and never trailing seconds on anything larger,
  // because a countdown that only re-renders on load reads as a frozen timer when it shows
  // them (the reasoning behind `coarseDuration` in desk's useSLA.ts).
  function duration(seconds: number) {
    return units(seconds)
      .map(([value, unit]) => `${value}${unit}`)
      .join(' ') || '0s'
  }

  /** The largest unit with anything in it, plus the one below it — and only that one, so a
   *  span of 83 days and 59 minutes reads as "83 days" rather than skipping the empty hours
   *  to pair two units that were never adjacent. */
  function units(seconds: number) {
    const all = [
      [Math.floor(seconds / 86400), 'd'],
      [Math.floor((seconds % 86400) / 3600), 'h'],
      [Math.floor((seconds % 3600) / 60), 'm'],
      [Math.floor(seconds % 60), 's'],
    ]
    const largest = all.findIndex(([value]) => value)
    if (largest < 0) return []
    return all.slice(largest, largest + 2).filter(([value]) => value)
  }

  return {
    identity,
    statusPill,
    basics,
    timeline,
  }
}
