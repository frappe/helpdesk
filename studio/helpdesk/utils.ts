import type { Ref } from 'vue'
import { FileUploadHandler, call, dialog, toast } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { dateTooltipFormat } from '@framework/ui/components/ActivityTimeline/utils'

// Private: an attachment on a support ticket is not public content.
const UPLOAD_ARGS = { folder: 'Home/Helpdesk', private: true }

export const DATE_FORMATS = {
  tooltip: dateTooltipFormat,
  clock: 'h:mm A',
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

export function parseJsonArray(value: unknown): any[] {
  const parsed = parseJson(value, [])
  return Array.isArray(parsed) ? parsed : []
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
  return call('frappe.client.set_value', { doctype: 'HD Ticket', name, fieldname: values })
}

// Keeps the files that made it; one file over the size limit must not sink the rest.
export async function uploadFiles(files: File[], args: Record<string, unknown> = UPLOAD_ARGS) {
  const results = await Promise.allSettled(
    files.map((file) => new FileUploadHandler().upload(file, args)),
  )
  const uploaded = results
    .filter((result) => result.status === 'fulfilled')
    .map((result: any) => result.value)
  const failedCount = files.length - uploaded.length
  if (failedCount) toast.error(countLabel(failedCount, '1 file could not be uploaded', '{0} files could not be uploaded'))
  return uploaded
}

export function countLabel(count: number, singular: string, plural: string) {
  return count === 1 ? __(singular) : __(plural, [count])
}

export function matchesQuery(query: string, ...fields: (string | undefined)[]) {
  const needle = query.trim().toLowerCase()
  return !needle || fields.join(' ').toLowerCase().includes(needle)
}
