import { computed } from 'vue'
import { dayjs, dayjsLocal } from 'frappe-ui'
import { dateFormat } from '@framework/ui/components/ActivityTimeline/utils'
import { __ } from '@helpdesk/shared/translation'
import { DATE_FORMATS, isSlaMissed, twoUnitDuration } from '@helpdesk/shared/utils'
import { useSession } from '@app/stores/session'
import { isClosedStatus, isResolvedStatus, statusMeta } from '@app/stores/ticketMeta'

const MINUTE = 60
// A reply inside this window reads as "someone was already there", not as a measured wait.
const IMMEDIATE_SECONDS = 5 * MINUTE

export function useTicketDetails(ticket, thread, statusChanges) {
  const session = useSession()
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
      { label: __('Priority'), value: data.value.priority, isPriority: true },
      ...templateFields(),
    ].filter((row) => row.value),
  )

  function templateFields() {
    return (data.value.template?.fields || [])
      // The heading carries the subject; Team and Priority are listed above.
      .filter((field) => !['subject', 'agent_group', 'priority'].includes(field.fieldname))
      .map((field) => ({ label: __(field.label), value: formatValue(field, data.value[field.fieldname]) }))
  }

  function formatValue(field, value) {
    if (!value) return value
    if (field.fieldtype === 'Date') return dayjs(value).format(session.dateFormat.value)
    if (field.fieldtype === 'Datetime') return dateFormat(value)
    return value
  }

  const timeline = computed(() => {
    // A close's history decides its steps, so wait for it rather than redraw them when it lands.
    if (isClosedStatus(data.value.status) && !statusChanges.data) return []
    const steps = [received(), ...assigned(), ...answered(), ...resolution(), ...closing()]
    // Ring the first unmet step after the last one reached.
    const reached = steps.findLastIndex((step) => step.state === 'done' || step.state === 'closed')
    const next = steps.slice(reached + 1).find((step) => step.state === 'pending')
    if (next) {
      next.state = 'next'
      // A paused status stops the SLA clock, so no due date applies; it is not always the customer's turn.
      if (data.value.status_category === 'Paused') {
        next.subtitle = __('On hold')
        next.late = false
      }
    }
    return steps
  })

  function received() {
    const on = data.value.creation
    return makeStep(__('Request received'), on ? dayjsLocal(on).format(DATE_FORMATS.step) : '', 'done', on)
  }

  function assigned() {
    const on = data.value.assigned_on
    if (on) return [makeStep(__('Assigned to agent'), elapsedPhrase(on), 'done', on)]
    // A reply or an ended ticket means it was handled without an assignment.
    if (thread.firstAgentReply.value || data.value.status_category === 'Resolved') return []
    return [makeStep(__('Awaiting assignment'), '', 'pending')]
  }

  function answered() {
    const reply = thread.firstAgentReply.value
    if (!reply) {
      // Nothing is owed on a ticket that has ended.
      if (data.value.status_category === 'Resolved') return []
      return [awaiting(__('First response'), data.value.response_by, data.value.overdue_by?.response)]
    }
    const summary = durationSummary(reply.creation, __('Answered immediately'), (took) => __('Answered in {0}', [took]))
    return [reachedStep(__('First response'), summary, reply.creation, data.value.response_by, data.value.first_response_failed_by)]
  }

  // Closing straight from an open status stamps `resolution_date` too, so the close covers it alone.
  function resolution() {
    const on = data.value.resolution_date
    if (data.value.status_category !== 'Resolved') return [awaiting(__('Resolution'), data.value.resolution_by, data.value.overdue_by?.resolution)]
    if (!on || closedOutright()) return []
    const summary = durationSummary(on, __('Resolved immediately'), (took) => __('Resolved in {0}', [took]))
    return [reachedStep(__('Resolution'), summary, on, data.value.resolution_by, data.value.resolution_failed_by)]
  }

  const lastClose = computed(() =>
    (statusChanges.data || []).findLast((change) => change.field === 'status' && isClosedStatus(change.to)),
  )

  function closedOutright() {
    return isClosedStatus(data.value.status) && Boolean(lastClose.value) && !isResolvedStatus(lastClose.value.from)
  }

  // `resolution_date` keeps the resolve's time through a close, so the status history dates it.
  function closing() {
    if (!isClosedStatus(data.value.status)) return []
    const on = lastClose.value?.on || data.value.resolution_date
    const late = isSlaMissed(data.value.resolution_date || on, data.value.resolution_by)
    const subtitle = [on && elapsedPhrase(on), late && __('SLA failed')].filter(Boolean).join(' · ')
    return [makeStep(__('Closed'), subtitle, 'done', on, late)]
  }

  // `overdueBy` is in business hours, from the server: only it knows the SLA's working hours and holidays.
  function awaiting(title: string, due: string, overdueBy?: number | null) {
    if (!due) return makeStep(title, '', 'pending')
    if (overdueBy != null) {
      return makeStep(title, __('Overdue by {0}', [formatMinutes(Math.max(overdueBy, MINUTE))]), 'pending', undefined, true)
    }
    return makeStep(title, __('Due {0}', [dueWording(due)]), 'pending')
  }

  function makeStep(title: string, subtitle: string, state: string, on?: string, late = false) {
    return { title, subtitle, state, late, fullDate: dateFormat(on) }
  }

  function durationSummary(on: string, immediate: string, tookWording: (took: string) => string) {
    const seconds = secondsSinceCreation(on)
    return seconds <= IMMEDIATE_SECONDS ? immediate : tookWording(formatMinutes(seconds))
  }

  // Late by the server's rule, the same one the desk shows: any time past due. `failedBy` is the
  // server's business-hours figure, re-measured on every save against the current SLA.
  function reachedStep(title: string, summary: string, on: string, due: string, failedBy: number) {
    if (!isSlaMissed(on, due)) return makeStep(title, summary, 'done', on)
    const late = Math.max(failedBy || 0, 1)
    const lateBy = late < MINUTE ? twoUnitDuration(late * 1000) : formatMinutes(late)
    return makeStep(title, `${summary} · ${__('{0} late', [lateBy])}`, 'done', on, true)
  }

  function elapsedPhrase(on: string) {
    const seconds = secondsSinceCreation(on)
    return seconds <= IMMEDIATE_SECONDS ? __('moments ago') : __('{0} later', [formatMinutes(seconds)])
  }

  function secondsSinceCreation(on: string) {
    return Math.max(dayjs(on).diff(dayjs(data.value.creation), 's'), 0)
  }

  function dueWording(target: string) {
    const due = dayjsLocal(target)
    const clock = due.format(DATE_FORMATS.clock)
    if (due.isSame(dayjsLocal(), 'day')) return __('{0} today', [clock])
    if (due.isSame(dayjsLocal().add(1, 'day'), 'day')) return __('{0} tomorrow', [clock])
    return due.format(DATE_FORMATS.step)
  }

  // Whole minutes: the sidebar renders on load only, and seconds would read as a stopped clock.
  function formatMinutes(seconds: number) {
    return twoUnitDuration(Math.floor(seconds / MINUTE) * MINUTE * 1000)
  }

  return { identity, statusPill, basics, timeline }
}
