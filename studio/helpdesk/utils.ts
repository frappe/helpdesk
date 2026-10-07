import type { Ref } from 'vue'
import { call, dialog, toast } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { dateTooltipFormat } from '@framework/ui/components/ActivityTimeline/utils'

export const SEARCH_DEBOUNCE_MS = 300

export const DATE_FORMATS = {
  tooltip: dateTooltipFormat,
  clock: 'h:mm A',
  short: 'D MMM YYYY',
  step: 'ddd D MMM, h:mm A',
  date: 'DD-MM-YYYY',
}

export function parseJson(value: unknown, fallback: any = undefined) {
  if (!value) return fallback
  if (typeof value !== 'string') return value
  try {
    return JSON.parse(value) ?? fallback
  } catch {
    return fallback
  }
}

export function errorMessage(error: any, fallback: string) {
  return error?.messages?.join(', ') || error?.message || fallback
}

type ActionOptions = { busy?: Ref<boolean>; success?: string; fallback: string }

export async function runAction(action: () => Promise<unknown>, options: ActionOptions) {
  const { busy, success, fallback } = options
  if (busy?.value) return
  if (busy) busy.value = true
  try {
    await action()
    if (success) toast.success(success)
  } catch (error) {
    console.error(error)
    toast.error(errorMessage(error, fallback))
  } finally {
    if (busy) busy.value = false
  }
}

export function setValues(doctype: string, name: string, values: Record<string, unknown>) {
  return call('frappe.client.set_value', { doctype, name, fieldname: values })
}

// `$dialog` for form scripts: their actions call `close()` or `close.close()`, as on the desk.
export function scriptDialog({ title, message, size, icon, actions }) {
  return dialog.confirm({
    title,
    message,
    size,
    icon,
    actions: actions?.map((action) => ({
      ...action,
      onClick: action.onClick && (({ close }) => action.onClick(Object.assign(() => close(), { close }))),
    })),
  })
}

export function askConfirm({ title, message, label, theme, action }) {
  return dialog.confirm({ title, message, theme, confirmLabel: label, cancelLabel: __('Cancel'), onConfirm: action })
}

export function updateTicket(name: string, values: Record<string, unknown>) {
  return setValues('HD Ticket', name, values)
}

// Takes strings already passed through `__()`, so the extractor sees the literals.
export function countLabel(count: number, singular: string, plural: string) {
  return count === 1 ? singular : plural.replace('{0}', String(count))
}

export function matchesQuery(query: string, ...fields: (string | undefined)[]) {
  const needle = query.trim().toLowerCase()
  return !needle || fields.join(' ').toLowerCase().includes(needle)
}
