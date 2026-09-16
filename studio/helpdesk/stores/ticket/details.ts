import { computed } from 'vue'
import { compactDuration, parseJsonArray } from '@app/utils'
import { dayjs } from 'frappe-ui'
import { statusMeta } from '@app/components/list/ticketCells'
import { t, tFormat } from '@app/stores/translations'

// Everything the summary sidebar shows, finished for display — the Studio blocks only bind.
// Read as progress, not as a report card: "Failed" is no use to the person still waiting.

const DATE_FORMAT = 'ddd, MMM D, YYYY h:mm A'
const STEP_FORMAT = 'ddd D MMM, h:mm a'
const DUE_FORMAT = 'ddd D MMM, h:mm a'
const CLOCK_FORMAT = 'h:mm a'
const EMPTY = '—'
// The page heading already carries the subject.
const HIDDEN_FIELDS = ['subject']
// A reply inside this window reads as "someone was already there", not as a measured wait.
const IMMEDIATE_SECONDS = 5 * 60

export function useTicketDetails(ticket, thread) {
  const data = computed(() => ticket.data || {})
  const firstReply = computed(() => thread?.firstAgentReply.value)

  // `via_customer_portal` is the only channel HD Ticket records; the rest is mail.
  const identity = computed(() => ({
    // A Contact is named by whatever created it; the real name lives in `full_name`.
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

  const statusPill = computed(() => statusMeta(data.value.status))

  const basics = computed(() => [
    { label: t('Team'), value: data.value.agent_group || EMPTY },
    { label: t('Priority'), value: data.value.priority || EMPTY },
    ...templateFields(),
  ])

  // An empty field keeps its row; a missing row would just look complete.
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

  // Milestones only — the thread on the left already is the messages.
  const timeline = computed(() => {
    const steps = [received(), assigned(), answered(), ...resolution(), ...closing()]
    // Ring the first unmet step past everything reached; later steps overtake earlier ones.
    let reached = -1
    steps.forEach((step, index) => {
      if (step.state === 'done' || step.state === 'closed') reached = index
    })
    const next = steps.slice(reached + 1).find((step) => step.state === 'pending')
    if (next) next.state = 'next'
    return steps
  })

  function received() {
    return step(t('Request received'), at(data.value.creation), 'done', data.value.creation)
  }

  // No assignment timestamp is customer-readable, so the first agent reply stands in.
  function assigned() {
    const reply = firstReply.value
    if (reply)
      return step(tFormat('Assigned to', reply.sender), since(reply.creation), 'done', reply.creation)
    if (assignees().length)
      return step(t('Assigned to agent'), t('An agent is on it'), 'done')
    return step(t('Assigned to agent'), t('Waiting to be assigned'), 'pending')
  }

  function assignees() {
    return parseJsonArray(data.value._assign)
  }

  function answered() {
    const reply = firstReply.value
    if (!reply) return awaiting(t('Awaiting first response'), data.value.response_by)
    return step(t('First response'), speedOf(reply), 'done', reply.creation)
  }

  function speedOf(reply) {
    const waited = Math.max(dayjs(reply.creation).diff(dayjs(data.value.creation), 's'), 0)
    const answered =
      waited <= IMMEDIATE_SECONDS ? 'Answered immediately' : `Answered in ${compactDuration(waited)}`
    return withLateness(
      answered,
      lateBy(reply.creation, data.value.response_by, data.value.first_response_failed_by),
    )
  }

  // A ticket that ended without being resolved gets no resolved step; the close covers it.
  function resolution() {
    const on = data.value.resolution_date
    if (on) return wasResolved() ? [step(t('Resolved'), resolvedAt(on), 'done', on)] : []
    if (!firstReply.value) return [step(t('Resolved'), '', 'pending')]
    return [awaiting(t('Awaiting resolution'), data.value.resolution_by)]
  }

  // A ticket closed outright is stamped `resolution_date` too, so the date alone can't tell.
  function wasResolved() {
    return data.value.status !== 'Closed' || Boolean(data.value.resolution_details)
  }

  function resolvedAt(on: string) {
    const took = Math.max(dayjs(on).diff(dayjs(data.value.creation), 's'), 0)
    const taken = took <= IMMEDIATE_SECONDS ? 'Resolved immediately' : `Resolved in ${compactDuration(took)}`
    return withLateness(
      taken,
      lateBy(on, data.value.resolution_by, data.value.resolution_failed_by),
    )
  }

  function withLateness(said: string, by: number) {
    return by ? `${said} · ${compactDuration(by)} late` : said
  }

  function lateBy(on: string, due: string, failedBy: number) {
    // The SLA's own figure is business-hours and written only on an actual miss.
    if (failedBy) return failedBy
    if (!due || !dayjs(on).isAfter(dayjs(due))) return 0
    return dayjs(on).diff(dayjs(due), 's')
  }

  function closing() {
    if (data.value.status !== 'Closed') return []
    const on = data.value.resolution_date
    // Resolved first: that stamp belongs to the step above, and nothing records the close.
    return [step(t('Closed'), wasResolved() ? '' : since(on), 'closed', wasResolved() ? '' : on)]
  }

  // Always `pending`, so the frontier logic above gives it the ring.
  function awaiting(title: string, due: string) {
    if (!due) return step(title, t('Pending'), 'pending')
    if (dayjs().isAfter(dayjs(due))) return step(title, `Overdue by ${countdown(due)}`, 'pending')
    return step(title, `Due ${dueWording(due)}`, 'pending')
  }

  // The stamp waits under the pointer; the visible line is elapsed wording.
  function step(title: string, subtitle: string, state: string, on?: string) {
    return { title, subtitle, state, fullDate: on ? dayjs(on).format(DATE_FORMAT) : '' }
  }

  function since(on: string) {
    const elapsed = Math.max(dayjs(on).diff(dayjs(data.value.creation), 's'), 0)
    return elapsed <= IMMEDIATE_SECONDS ? 'moments later' : `${compactDuration(elapsed)} later`
  }

  function at(value: string) {
    return value ? dayjs(value).format(STEP_FORMAT) : ''
  }

  function dueWording(target: string) {
    const due = dayjs(target)
    if (due.isSame(dayjs(), 'day')) return `${due.format(CLOCK_FORMAT)} today`
    if (due.isSame(dayjs().add(1, 'day'), 'day')) return `${due.format(CLOCK_FORMAT)} tomorrow`
    return due.format(DUE_FORMAT)
  }

  function countdown(target: string) {
    return compactDuration(Math.abs(dayjs(target).diff(dayjs(), 's')))
  }

  return {
    identity,
    statusPill,
    basics,
    timeline,
  }
}
