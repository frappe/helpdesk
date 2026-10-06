import { computed } from 'vue'
import { dayjs } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { twoUnitDuration } from '@helpdesk/shared/utils'
import { isClosedStatus, statusMeta } from '@app/stores/ticketMeta'
import { DATE_FORMATS } from '@app/utils'

// The summary sidebar, worded as progress rather than as a report card.

const MINUTE = 60
// A reply inside this window reads as "someone was already there", not as a measured wait.
const IMMEDIATE_SECONDS = 5 * MINUTE

export function useTicketDetails(ticket, thread) {
  const data = computed(() => ticket.data || {})

  const identity = computed(() => ({
    // A Contact is named by whatever created it; the real name lives in `full_name`.
    name:
      data.value.contact?.full_name ||
      data.value.contact?.name ||
      data.value.raised_by ||
      '',
    image: data.value.contact?.image || '',
    reference: data.value.name ? `#${data.value.name}` : '',
  }))

  const statusPill = computed(() => statusMeta(data.value.status))

  const basics = computed(() =>
    [
      { label: __('Team'), value: data.value.agent_group },
      { label: __('Priority'), value: data.value.priority },
      ...templateFields(),
    ].filter((row) => row.value),
  )

  function templateFields() {
    return (data.value.template?.fields || [])
      // The page heading already carries the subject.
      .filter((field) => field.fieldname !== 'subject')
      .map((field) => ({
        label: __(field.label),
        value: formatValue(field, data.value[field.fieldname]),
      }))
  }

  function formatValue(field, value) {
    if (!value) return value
    if (field.fieldtype === 'Date') return dayjs(value).format(DATE_FORMATS.date)
    if (field.fieldtype === 'Datetime') return dayjs(value).format(DATE_FORMATS.tooltip)
    return value
  }

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
    const on = data.value.creation
    return makeStep(__('Request received'), formatStepDate(on), 'done', on)
  }

  // Assignment is agent-only data, so the first agent reply stands in for it.
  function assigned() {
    const reply = thread.firstAgentReply.value
    if (reply)
      return makeStep(__('Assigned to agent'), elapsedPhrase(reply.creation), 'done', reply.creation)
    return makeStep(__('Assigned to agent'), __('Waiting to be assigned'), 'pending')
  }

  function answered() {
    const reply = thread.firstAgentReply.value
    if (!reply) return awaiting(__('Awaiting first response'), data.value.response_by)
    return makeStep(__('First response'), firstResponseSummary(reply.creation), 'done', reply.creation)
  }

  function firstResponseSummary(on: string) {
    const waited = secondsSinceCreation(on)
    const summary =
      waited <= IMMEDIATE_SECONDS
        ? __('Answered immediately')
        : __('Answered in {0}', [formatMinutes(waited)])
    return appendLateness(
      summary,
      secondsLate(on, data.value.response_by, data.value.first_response_failed_by),
    )
  }

  // A ticket that ended without being resolved gets no resolved step; the close covers it.
  function resolution() {
    const on = data.value.resolution_date
    if (on) return wasResolved() ? [makeStep(__('Resolved'), resolutionSummary(on), 'done', on)] : []
    if (!thread.firstAgentReply.value) return [makeStep(__('Resolved'), '', 'pending')]
    return [awaiting(__('Awaiting resolution'), data.value.resolution_by)]
  }

  // A ticket closed outright is stamped `resolution_date` too, so the date alone can't tell.
  function wasResolved() {
    return !isClosedStatus(data.value.status) || Boolean(data.value.resolution_details)
  }

  function resolutionSummary(on: string) {
    const took = secondsSinceCreation(on)
    const summary =
      took <= IMMEDIATE_SECONDS
        ? __('Resolved immediately')
        : __('Resolved in {0}', [formatMinutes(took)])
    return appendLateness(
      summary,
      secondsLate(on, data.value.resolution_by, data.value.resolution_failed_by),
    )
  }

  function appendLateness(summary: string, seconds: number) {
    return seconds >= MINUTE ? `${summary} · ${__('{0} late', [formatMinutes(seconds)])}` : summary
  }

  function secondsLate(on: string, due: string, failedBy: number) {
    // The SLA's own figure is business-hours and written only on an actual miss.
    if (failedBy) return failedBy
    if (!due || !dayjs(on).isAfter(dayjs(due))) return 0
    return dayjs(on).diff(dayjs(due), 's')
  }

  function closing() {
    if (!isClosedStatus(data.value.status)) return []
    const on = data.value.resolution_date
    // Resolved first: that stamp belongs to the step above, and nothing records the close.
    if (wasResolved()) return [makeStep(__('Closed'), '', 'closed')]
    return [makeStep(__('Closed'), elapsedPhrase(on), 'closed', on)]
  }

  function awaiting(title: string, due: string) {
    if (!due) return makeStep(title, __('Pending'), 'pending')
    if (dayjs().isAfter(dayjs(due)))
      return makeStep(title, __('Overdue by {0}', [formatTimeUntil(due)]), 'pending')
    return makeStep(title, __('Due {0}', [dueWording(due)]), 'pending')
  }

  function makeStep(title: string, subtitle: string, state: string, on?: string) {
    return { title, subtitle, state, fullDate: on ? dayjs(on).format(DATE_FORMATS.tooltip) : '' }
  }

  function elapsedPhrase(on: string) {
    const elapsed = secondsSinceCreation(on)
    return elapsed <= IMMEDIATE_SECONDS
      ? __('moments later')
      : __('{0} later', [formatMinutes(elapsed)])
  }

  function secondsSinceCreation(on: string) {
    return Math.max(dayjs(on).diff(dayjs(data.value.creation), 's'), 0)
  }

  function formatStepDate(value: string) {
    return value ? dayjs(value).format(DATE_FORMATS.step) : ''
  }

  function dueWording(target: string) {
    const due = dayjs(target)
    if (due.isSame(dayjs(), 'day')) return __('{0} today', [due.format(DATE_FORMATS.clock)])
    if (due.isSame(dayjs().add(1, 'day'), 'day'))
      return __('{0} tomorrow', [due.format(DATE_FORMATS.clock)])
    return due.format(DATE_FORMATS.step)
  }

  function formatTimeUntil(target: string) {
    return formatMinutes(Math.abs(dayjs(target).diff(dayjs(), 's')))
  }

  // Whole minutes: the sidebar re-renders only on load, and seconds would read as a stopped clock.
  function formatMinutes(seconds: number) {
    return twoUnitDuration(Math.floor(seconds / MINUTE) * MINUTE * 1000)
  }

  return {
    identity,
    statusPill,
    basics,
    timeline,
  }
}
