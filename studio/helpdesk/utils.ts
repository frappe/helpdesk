import type { Ref } from 'vue'
import { useClipboard } from '@vueuse/core'
import { call, dialog, toast } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { getErrorMessage } from '@helpdesk/shared/utils'
import { setupCustomizations, withLegacyCloseContext } from '@helpdesk/shared/formScripts'

export const SEARCH_DEBOUNCE_MS = 300

// Mirrors frappe.handler.ALLOWED_MIMETYPES, which the server enforces for users without desk access.
const CUSTOMER_FILE_TYPES = [
  '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.txt', '.csv', '.mov', '.mp4',
  '.doc', '.docx', '.xls', '.xlsx', '.odt', '.ods',
]

// Undefined for agents, who may upload anything.
export function uploadableFileTypes(isAgent: boolean) {
  return isAgent ? undefined : CUSTOMER_FILE_TYPES
}

export const DATE_FORMATS = {
  clock: 'h:mm A',
  short: 'D MMM YYYY',
  step: 'ddd D MMM, h:mm A',
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

export type ActionOptions = { busy?: Ref<boolean>; success?: string; fallback: string }

export async function runAction(action: () => Promise<unknown>, options: ActionOptions) {
  const { busy, success, fallback } = options
  if (busy?.value) return
  if (busy) busy.value = true
  try {
    await action()
    if (success) toast.success(success)
    return true
  } catch (error) {
    console.error(error)
    getErrorMessage(error, true, fallback)
  } finally {
    if (busy) busy.value = false
  }
}

export function setValues(doctype: string, name: string, values: Record<string, unknown>) {
  return call('frappe.client.set_value', { doctype, name, fieldname: values })
}

// `$dialog` for form scripts: their actions call `close()` or `close.close()`, as on the desk.
function scriptDialog({ title, message, size, icon, actions }) {
  return dialog.confirm({
    title,
    message,
    size,
    icon,
    actions: withLegacyCloseContext(actions),
  })
}

// HD Form Scripts get the desk portal's context, so scripts written for it keep working.
export async function runFormScripts(data, context, extra: Record<string, unknown> = {}) {
  await setupCustomizations(data, { call: context.call, router: context.router, $dialog: scriptDialog, ...extra })
  return data._customActions || []
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

// "Category · 3 min read"; either part may be missing.
export function articleMeta(categoryName?: string, minutes?: number) {
  const readTime = minutes ? countLabel(minutes, __('1 min read'), __('{0} min read')) : ''
  return [categoryName, readTime].filter(Boolean).join(' · ')
}

// `legacy`: execCommand fallback where the Clipboard API is missing (plain http).
export async function copyPageLink() {
  await useClipboard({ legacy: true }).copy(window.location.href)
  toast.success(__('Link copied'))
}

export function matchesQuery(query: string, ...fields: (string | undefined)[]) {
  const needle = query.trim().toLowerCase()
  return !needle || fields.join(' ').toLowerCase().includes(needle)
}
