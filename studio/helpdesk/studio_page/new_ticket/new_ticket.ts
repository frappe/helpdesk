import { computed, reactive, ref, watch } from 'vue'
import { useFileUpload } from 'frappe-ui'
import { evaluateDependsOn } from '@framework/ui/FormLayout'
import { applyFieldFilters } from '@helpdesk/shared/formScripts'
import { __ } from '@helpdesk/shared/translation'
import { isContentEmpty, parseLinkFilters } from '@helpdesk/shared/utils'
import ApiOptionsField from '@app/components/common/ApiOptionsField.vue'
import { ROUTES } from '@helpdesk/shared/portalRoutes'
import { navigateTo } from '@app/stores/router'
import { useSettingsModal } from '@app/stores/settings'
import { getPriority, loadTicketMeta } from '@app/stores/ticketMeta'
import { runAction, runFormScripts, uploadableFileTypes } from '@app/utils'
import { useArticleSearch } from '@app/composables/useArticleSearch'

const DEFAULT_TEMPLATE = 'Default'
const UPLOAD_FOLDER = 'Home/Helpdesk'
const SUGGESTION_LIMIT = 3

export default function setup(context) {
  const { subject, description, template, newTicket, route } = context
  const settings = useSettingsModal(context)

  // A ticket raised from search starts from what was searched.
  const searched = String(route?.query?.q || '').trim()
  // The subject holds 140 characters; a longer search would leave a form that can't be sent.
  if (searched && !subject.value) subject.value = searched.slice(0, 140)

  const model = reactive({})
  const attachments = ref([])
  const isCreating = ref(false)
  const uploading = ref(0)

  // The upload queue keeps only `file_url`; the server links attachments by File name.
  const uploadedByUrl = new Map()

  const uploadRestrictions = computed(() => ({ allowed_file_types: uploadableFileTypes(settings.isAgent.value) }))

  function uploadPrivately(file, _args, { signal, onProgress }) {
    uploading.value += 1
    return useFileUpload()
      .upload(file, {
        private: true,
        folder: UPLOAD_FOLDER,
        signal,
        onProgress: ({ loaded, total }) => onProgress(loaded, total),
      })
      .then((doc) => {
        uploadedByUrl.set(doc.file_url, doc)
        return doc
      })
      .finally(() => (uploading.value -= 1))
  }

  // The editor's own default, counted, so a ticket is never created around a half-uploaded image.
  function uploadInline(file) {
    uploading.value += 1
    return useFileUpload()
      .upload(file, { private: true })
      .finally(() => (uploading.value -= 1))
  }

  template.fetch()
  loadTicketMeta()

  const customActions = ref([])
  // The template's own fields, for `applyFilters` to restore once a filter is lifted.
  let oldFields = []

  watch(
    () => template.data,
    async (data) => {
      if (!data) return
      if (data.description_template && isContentEmpty(description.value)) {
        description.value = data.description_template
      }
      oldFields = JSON.parse(JSON.stringify(data.fields || []))
      // Field dependency rules compare with '' (`doc.priority != ''`), which undefined passes.
      for (const row of data.fields || []) model[row.fieldname] ??= ''
      customActions.value = await runFormScripts(data, context, { doc: model, applyFilters })
    },
    { immediate: true },
  )

  function applyFilters(fieldname: string, filters: any = null) {
    applyFieldFilters(template.data.fields, fieldname, filters, model, oldFields)
  }

  // A script's `onChange` handlers for a field, run when its value is committed.
  function scriptListeners(row) {
    const handlers = template.data?._customOnChange?.[row.fieldname]
    if (!handlers) return undefined
    return { change: (value) => handlers.forEach((handler) => handler(value, row.fieldtype)) }
  }

  const about = computed(() => template.data?.about || '')

  const suggestions = useArticleSearch(subject, { limit: SUGGESTION_LIMIT })

  // TextEditor has no `modelValue`, so Studio's automatic binding never fires.
  function setDescription(html) {
    description.value = html
  }

  const { dateFormat } = settings
  const timeFormat = computed(() => settings.config.value?.time_format)

  // As on the desk's form, only priority shows its description.
  const priorityHint = computed(() => getPriority(model.priority)?.description?.trim() || undefined)

  // The desk's fallback when the template sets no placeholder.
  function defaultPlaceholder(fieldtype) {
    return ['Select', 'Link', 'Check'].includes(fieldtype) ? __('Select an option') : __('Type something')
  }

  // Site date formats reach the pickers as attrs; unset until the config arrives.
  function uiFor(row) {
    if (row.url_method) return { component: ApiOptionsField, props: { url: row.url_method } }
    if (!dateFormat.value) return undefined
    if (row.fieldtype === 'Datetime') return { props: { format: `${dateFormat.value} ${timeFormat.value}` } }
    if (row.fieldtype === 'Date') return { props: { format: dateFormat.value } }
  }

  const fields = computed(() =>
    (template.data?.fields || []).map((row) => ({
      fieldname: row.fieldname,
      fieldtype: row.fieldtype,
      label: __(row.label),
      options: row.options,
      reqd: Boolean(row.required),
      placeholder: row.placeholder || defaultPlaceholder(row.fieldtype),
      description: row.fieldname === 'priority' ? priorityHint.value : undefined,
      dependsOn: row.depends_on,
      mandatoryDependsOn: row.mandatory_depends_on,
      filters: row.link_filters ? parseLinkFilters(row.link_filters) : undefined,
      readOnly: Boolean(row.disabled),
      ui: { ...uiFor(row), on: scriptListeners(row) },
    })),
  )

  // Visible fields alternate across up to three columns, which would stack out of order on a phone.
  const layout = computed(() => {
    const visible = fields.value.filter((field) => evaluateDependsOn(field.dependsOn, model))
    const count = settings.isPhone.value ? 1 : Math.min(3, visible.length)
    const columns = Array.from({ length: count }, (_, column) => ({
      fields: visible.filter((_, index) => index % count === column),
    }))
    return [{ sections: [{ hideLabel: true, hideBorder: true, columns }] }]
  })

  const canSubmit = computed(() => {
    if (uploading.value || !subject.value || isContentEmpty(description.value)) return false
    return fields.value
      .filter((field) => evaluateDependsOn(field.dependsOn, model) && isRequired(field))
      .every((field) => model[field.fieldname])
  })

  function isRequired(field) {
    return field.reqd || (field.mandatoryDependsOn && evaluateDependsOn(field.mandatoryDependsOn, model))
  }

  // Sent even when empty: an origin marks a portal ticket, and no `from` is a Direct visit.
  function currentOrigin() {
    const { from, article, q } = route?.query || {}
    return { from, article, q }
  }

  function createTicket() {
    if (!canSubmit.value) return
    return runAction(
      async () => {
        const ticket = await newTicket.submit({
          doc: {
            subject: subject.value,
            description: description.value,
            template: DEFAULT_TEMPLATE,
            ...model,
          },
          attachments: attachments.value.map((file) => uploadedByUrl.get(file.file_url)),
          origin: currentOrigin(),
        })
        await navigateTo(ROUTES.ticket(ticket.name))
      },
      { busy: isCreating, fallback: __('Could not create the ticket') },
    )
  }

  return {
    ...settings,
    customActions,
    about,
    suggestions,
    fields,
    layout,
    model,
    setDescription,
    canSubmit,
    attachments,
    uploadPrivately,
    uploadInline,
    uploadRestrictions,
    isCreating,
    createTicket,
  }
}
