import { computed } from 'vue'
import { dayjs } from 'frappe-ui'
import { dateFormat, dayjsLocal } from '@helpdesk/shared/timezone'
import { __ } from '@helpdesk/shared/translation'
import { DATE_FORMATS, isSlaMissed, twoUnitDuration } from '@helpdesk/shared/utils'
import { useSession } from '@app/stores/session'
import { isClosedStatus, isResolvedStatus, statusMeta } from '@app/stores/ticketMeta'

const MINUTE = 60
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

// Every address valid, or none: one bad entry shows the raw text instead.
function parseEmails(value: unknown) {
  if (typeof value !== 'string') return null
  const emails = value
    .split(/[,;]/)
    .map((part) => part.trim())
    .filter(Boolean)
  return emails.length && emails.every((email) => EMAIL.test(email)) ? emails : null
}

export function useTicketDetails(ticket, thread, statusChanges) {
  const session = useSession()
  const data = computed(() => ticket.data || {})

  const identity = computed(() => ({
    // Contact docname is arbitrary; the person's name is `full_name`.
    name: data.value.contact?.full_name || data.value.contact?.name || data.value.raised_by || '',
    image: data.value.contact?.image || '',
    reference: data.value.name ? `#${data.value.name}` : '',
  }))

  const statusPill = computed(() => statusMeta(data.value.status))

  const basics = computed(() =>
    [
      // Always shown when set, whatever the template says.
      { label: __('Priority'), value: data.value.priority, isPriority: true },
      { label: __('Customer'), value: data.value.customer, isCustomer: true, image: data.value.customer_image || '' },
      { label: __('Team'), value: data.value.agent_group },
      ...templateFields(),
    ].filter((row) => row.value),
  )

  function templateFields() {
    return (data.value.template?.fields || [])
      // Subject is the heading; Customer, Team and Priority are listed above.
      .filter((field) => !['subject', 'customer', 'agent_group', 'priority'].includes(field.fieldname))
      .map((field) => {
        const value = formatValue(field, data.value[field.fieldname])
        return { label: __(field.label), value, emails: parseEmails(value) }
      })
  }

  function formatValue(field, value) {
    if (!value) return value
    if (field.fieldtype === 'Date') return dayjs(value).format(session.dateFormat.value)
    if (field.fieldtype === 'Datetime') return dateFormat(value)
    return value
  }

  const timeline = computed(() => {
    // Close history decides the steps; wait rather than redraw.
    if (isClosedStatus(data.value.status) && !statusChanges.data) return []
    const steps = [received(), ...assigned(), ...answered(), ...resolution(), ...closing()]
    const reached = steps.findLastIndex((step) => step.state === 'done' || step.state === 'closed')
    const next = steps.slice(reached + 1).find((step) => step.state === 'pending')
    if (next) {
      next.state = 'next'
      // Paused stops the SLA clock, so no due date applies.
      if (data.value.status_category === 'Paused') {
        next.subtitle = __('On hold')
        next.late = false
      }
    }
    return steps
  })

  function received() {
    const on = data.value.creation
    return makeStep(__('Request received'), stepDate(on), 'done', on)
  }

  function assigned() {
    const on = data.value.assigned_on
    if (on) return [makeStep(__('Assigned to agent'), stepDate(on), 'done', on)]
    // Replied: handled without an assignment.
    if (thread.firstAgentReply.value) return []
    if (isClosed()) return [skipped(__('Awaiting assignment'))]
    if (data.value.status_category === 'Resolved') return []
    // Late with the first response: no agent, no reply.
    const late = data.value.overdue_by?.response != null
    return [makeStep(__('Awaiting assignment'), waitingFor(), 'pending', undefined, late)]
  }

  // Open tickets only. Today's reads as a clock time.
  function waitingFor() {
    const since = dayjsLocal(data.value.creation)
    const when = since.isSame(dayjsLocal(), 'day') ? since.format(DATE_FORMATS.clock) : stepDate(data.value.creation)
    return __('Pending since {0}', [when])
  }

  function answered() {
    const reply = thread.firstAgentReply.value
    if (!reply) {
      if (isClosed()) return [skipped(__('First response'))]
      if (data.value.status_category === 'Resolved') return []
      return [awaiting(__('First response'), data.value.response_by, data.value.overdue_by?.response)]
    }
    return [reachedStep(__('First response'), reply.creation, data.value.response_by, data.value.first_response_failed_by)]
  }

  function resolution() {
    const on = data.value.resolution_date
    // Closing resolves too: a direct close reads as resolved at the close.
    if (isClosed() && (closedOutright() || !on))
      return [reachedStep(__('Resolution'), closedOn(), data.value.resolution_by, data.value.resolution_failed_by)]
    if (data.value.status_category !== 'Resolved') return [awaiting(__('Resolution'), data.value.resolution_by, data.value.overdue_by?.resolution)]
    if (!on) return []
    return [reachedStep(__('Resolution'), on, data.value.resolution_by, data.value.resolution_failed_by)]
  }

  const lastClose = computed(() =>
    (statusChanges.data || []).findLast((change) => change.field === 'status' && isClosedStatus(change.to)),
  )

  function isClosed() {
    return isClosedStatus(data.value.status)
  }

  function closedOutright() {
    return isClosedStatus(data.value.status) && Boolean(lastClose.value) && !isResolvedStatus(lastClose.value.from)
  }

  // `modified` stands in when nothing dates the close; wrong if edited after closing
  function closedOn() {
    return lastClose.value?.on || data.value.resolution_date || data.value.modified
  }

  // `resolution_date` keeps the resolve time; status history dates the close.
  function closing() {
    if (!isClosed()) return []
    const on = closedOn()
    const late = isSlaMissed(data.value.resolution_date || on, data.value.resolution_by)
    const subtitle = [late && __('SLA failed'), stepDate(on)]
      .filter(Boolean)
      .join(' · ')
    return [makeStep(__('Closed'), subtitle, 'done', on, late)]
  }

  // `overdueBy` comes from the server: only it knows SLA working hours.
  function awaiting(title: string, due: string, overdueBy?: number | null) {
    if (!due) return makeStep(title, '', 'pending')
    if (overdueBy != null) {
      return makeStep(title, __('Overdue by {0}', [formatMinutes(Math.max(overdueBy, MINUTE))]), 'pending', undefined, true)
    }
    return makeStep(title, __('Due {0}', [dueWording(due)]), 'pending')
  }

  // Never happened: the ticket closed first. No due date applies.
  function skipped(title: string) {
    return makeStep(title, __('Skipped'), 'skipped')
  }

  function makeStep(title: string, subtitle: string, state: string, on?: string, late = false) {
    return { title, subtitle, state, late, fullDate: dateFormat(on) }
  }

  // Late by the server's rule; `failedBy` is its business-hours figure.
  function reachedStep(title: string, on: string, due: string, failedBy: number) {
    const date = stepDate(on)
    if (!isSlaMissed(on, due)) return makeStep(title, date, 'done', on)
    const late = Math.max(failedBy || 0, 1)
    const lateBy = late < MINUTE ? twoUnitDuration(late * 1000) : formatMinutes(late)
    return makeStep(title, `${date} · ${__('{0} late', [lateBy])}`, 'done', on, true)
  }

  function stepDate(on?: string) {
    return on ? dayjsLocal(on).format(DATE_FORMATS.step) : ''
  }

  function dueWording(target: string) {
    const due = dayjsLocal(target)
    const clock = due.format(DATE_FORMATS.clock)
    if (due.isSame(dayjsLocal(), 'day')) return __('{0} today', [clock])
    if (due.isSame(dayjsLocal().add(1, 'day'), 'day')) return __('{0} tomorrow', [clock])
    return due.format(DATE_FORMATS.step)
  }

  // Whole minutes: rendered once, so seconds would look frozen.
  function formatMinutes(seconds: number) {
    return twoUnitDuration(Math.floor(seconds / MINUTE) * MINUTE * 1000)
  }

  return { identity, statusPill, basics, timeline }
}
