import { computed } from 'vue'
import { dayjs } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { twoUnitDuration } from '@helpdesk/shared/utils'
import { isClosedStatus, statusMeta } from '@app/stores/ticketMeta'
import { DATE_FORMATS } from '@app/utils'

const MINUTE = 60
// A reply inside this window reads as "someone was already there", not as a measured wait.
const IMMEDIATE_SECONDS = 5 * MINUTE

export function useTicketDetails(ticket, thread) {
  const data = computed(() => ticket.data || {})

  const identity = computed(() => ({
    // A Contact's docname is whatever created it; the person's name is `full_name`.
    name: data.value.contact?.full_name || data.value.contact?.name || data.value.raised_by || '',
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
      .map((field) => ({ label: __(field.label), value: formatValue(field, data.value[field.fieldname]) }))
  }

  function formatValue(field, value) {
    if (!value) return value
    if (field.fieldtype === 'Date') return dayjs(value).format(DATE_FORMATS.date)
    if (field.fieldtype === 'Datetime') return dayjs(value).format(DATE_FORMATS.tooltip)
    return value
  }

  const timeline = computed(() => {
    const steps = [received(), assigned(), answered(), ...resolution(), ...closing()]
    // Ring the first unmet step after the last one reached.
    const reached = steps.findLastIndex((step) => step.state === 'done' || step.state === 'closed')
    const next = steps.slice(reached + 1).find((step) => step.state === 'pending')
    if (next) next.state = 'next'
    return steps
  })

  function received() {
    const on = data.value.creation
    return makeStep(__('Request received'), on ? dayjs(on).format(DATE_FORMATS.step) : '', 'done', on)
  }

  // Assignment is agent-only data, so the first agent reply stands in for it.
  function assigned() {
    const reply = thread.firstAgentReply.value
    if (!reply) return makeStep(__('Assigned to agent'), __('Waiting to be assigned'), 'pending')
    return makeStep(__('Assigned to {0}', [reply.sender]), elapsedPhrase(reply.creation), 'done', reply.creation)
  }

  function answered() {
    const reply = thread.firstAgentReply.value
    if (!reply) return awaiting(__('Awaiting first response'), data.value.response_by)
    const summary = durationSummary(reply.creation, __('Answered immediately'), (took) => __('Answered in {0}', [took]))
    const late = secondsLate(reply.creation, data.value.response_by, data.value.first_response_failed_by)
    return makeStep(__('First response'), withLateness(summary, late), 'done', reply.creation)
  }

  // A ticket that ended without being resolved gets no resolved step; the close covers it.
  function resolution() {
    const on = data.value.resolution_date
    if (!on) {
      if (!thread.firstAgentReply.value) return [makeStep(__('Resolved'), '', 'pending')]
      return [awaiting(__('Awaiting resolution'), data.value.resolution_by)]
    }
    if (!wasResolved()) return []
    const summary = durationSummary(on, __('Resolved immediately'), (took) => __('Resolved in {0}', [took]))
    const late = secondsLate(on, data.value.resolution_by, data.value.resolution_failed_by)
    return [makeStep(__('Resolved'), withLateness(summary, late), 'done', on)]
  }

  // Closing outright stamps `resolution_date` too, so the date alone cannot tell.
  function wasResolved() {
    return !isClosedStatus(data.value.status) || Boolean(data.value.resolution_details)
  }

  function closing() {
    if (!isClosedStatus(data.value.status)) return []
    // When resolved first, the date belongs to that step and nothing records the close itself.
    if (wasResolved()) return [makeStep(__('Closed'), '', 'closed')]
    const on = data.value.resolution_date
    return [makeStep(__('Closed'), elapsedPhrase(on), 'closed', on)]
  }

  function awaiting(title: string, due: string) {
    if (!due) return makeStep(title, __('Pending'), 'pending')
    if (dayjs().isAfter(dayjs(due))) {
      return makeStep(title, __('Overdue by {0}', [formatMinutes(dayjs().diff(dayjs(due), 's'))]), 'pending')
    }
    return makeStep(title, __('Due {0}', [dueWording(due)]), 'pending')
  }

  function makeStep(title: string, subtitle: string, state: string, on?: string) {
    return { title, subtitle, state, fullDate: on ? dayjs(on).format(DATE_FORMATS.tooltip) : '' }
  }

  function durationSummary(on: string, immediate: string, tookWording: (took: string) => string) {
    const seconds = secondsSinceCreation(on)
    return seconds <= IMMEDIATE_SECONDS ? immediate : tookWording(formatMinutes(seconds))
  }

  function withLateness(summary: string, seconds: number) {
    return seconds >= MINUTE ? `${summary} · ${__('{0} late', [formatMinutes(seconds)])}` : summary
  }

  // The SLA's own figure counts business hours and is written only on an actual miss.
  function secondsLate(on: string, due: string, failedBy: number) {
    if (failedBy) return failedBy
    return due ? Math.max(dayjs(on).diff(dayjs(due), 's'), 0) : 0
  }

  function elapsedPhrase(on: string) {
    const seconds = secondsSinceCreation(on)
    return seconds <= IMMEDIATE_SECONDS ? __('moments later') : __('{0} later', [formatMinutes(seconds)])
  }

  function secondsSinceCreation(on: string) {
    return Math.max(dayjs(on).diff(dayjs(data.value.creation), 's'), 0)
  }

  function dueWording(target: string) {
    const due = dayjs(target)
    const clock = due.format(DATE_FORMATS.clock)
    if (due.isSame(dayjs(), 'day')) return __('{0} today', [clock])
    if (due.isSame(dayjs().add(1, 'day'), 'day')) return __('{0} tomorrow', [clock])
    return due.format(DATE_FORMATS.step)
  }

  // Whole minutes: the sidebar renders on load only, and seconds would read as a stopped clock.
  function formatMinutes(seconds: number) {
    return twoUnitDuration(Math.floor(seconds / MINUTE) * MINUTE * 1000)
  }

  return { identity, statusPill, basics, timeline }
}
