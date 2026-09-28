import type { Ref } from 'vue'
import { FileUploadHandler, call, toast } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { dateTooltipFormat } from '@helpdesk/shared/utils'

// Private: an attachment on a support ticket is not public content.
export const UPLOAD_ARGS = { folder: 'Home/Helpdesk', private: true }

export const DATE_FORMATS = {
  tooltip: dateTooltipFormat,
  clock: 'h:mm A',
  day: 'D MMMM',
  dayWithYear: 'D MMMM YYYY',
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

// Runs a request once at a time and reports how it went as a toast.
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

export function updateTicket(name: string, values: Record<string, unknown>) {
  return call('frappe.client.set_value', { doctype: 'HD Ticket', name, fieldname: values })
}

// Keeps the files that made it; one file over the size limit must not sink the rest.
// ponytail: @framework/ui useUploader is the upgrade if restrictions or progress are needed
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
