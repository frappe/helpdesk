import { computed, reactive, ref, watch } from 'vue'
import { createListResource, toast, useFileUpload } from 'frappe-ui'
import { evaluateDependsOn } from '@framework/ui/FormLayout'
import {
  handleLinkFieldUpdate,
  handleSelectFieldUpdate,
  setupCustomizations,
} from '@helpdesk/shared/formScripts'
import { __ } from '@helpdesk/shared/translation'
import { isContentEmpty, parseLinkFilters } from '@helpdesk/shared/utils'
import ApiOptionsField from '@app/components/common/ApiOptionsField.vue'
import { ROUTES } from '@app/routes'
import { navigateTo } from '@app/stores/router'
import { useSettingsModal } from '@app/stores/settings'
import { runAction, scriptDialog } from '@app/utils'

const DEFAULT_TEMPLATE = 'Default'
const UPLOAD_FOLDER = 'Home/Helpdesk'

// The upload queue keeps only `file_url`; the server links attachments by File name.
const uploadedByUrl = new Map()

function uploadPrivately(file, _args, { signal, onProgress }) {
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
}

export default function setup(context) {
  const { subject, description, template, newTicket, route } = context
  const session = useSettingsModal(context)

  const searched = String(route?.query?.subject || '').trim()
  if (searched && !subject.value) subject.value = searched

  const model = reactive({})

  const attachments = ref([])
  const isCreating = ref(false)

  const priorities = createListResource({
    doctype: 'HD Ticket Priority',
    fields: ['name', 'description'],
  })

  // Permission-gated, so fetched once the session is known: a guest would only 403.
  watch(
    session.isGuest,
    (isGuest) => {
      if (isGuest) return
      template.fetch()
      priorities.fetch()
    },
    { immediate: true },
  )

  watch(
    () => template.data,
    (data) => {
      if (data?.description_template && isContentEmpty(description.value)) {
        description.value = data.description_template
      }
    },
  )

  const customActions = ref([])
  // The template's own fields, for `applyFilters` to restore once a filter is lifted.
  let oldFields = []

  // HD Form Scripts get the desk portal's context, so scripts written for it keep working.
  watch(
    () => template.data,
    async (data) => {
      if (!data) return
      oldFields = JSON.parse(JSON.stringify(data.fields || []))
      await setupCustomizations(data, {
        doc: model,
        call: context.call,
        router: context.router,
        $dialog: scriptDialog,
        applyFilters,
      })
      customActions.value = data._customActions || []
    },
    { immediate: true },
  )

  function applyFilters(fieldname: string, filters: any = null) {
    const field = template.data.fields.find((row) => row.fieldname === fieldname)
    if (field?.fieldtype === 'Select') handleSelectFieldUpdate(field, fieldname, filters, model, oldFields)
    else if (field?.fieldtype === 'Link') handleLinkFieldUpdate(field, fieldname, filters, model, oldFields)
  }

  // A script's `onChange` handlers for a field, run when its value is committed.
  function scriptListeners(row) {
    const handlers = template.data?._customOnChange?.[row.fieldname]
    if (!handlers) return undefined
    return { change: (value) => handlers.forEach((handler) => handler(value, row.fieldtype)) }
  }

  const about = computed(() => template.data?.about || '')

  // TextEditor has no `modelValue`, so Studio's automatic binding never fires.
  function setDescription(html) {
    description.value = html
  }

  const dateFormat = computed(() => session.config.value?.date_format?.toUpperCase())
  const timeFormat = computed(() => session.config.value?.time_format)

  // Only a priority carries a description worth showing, as on the desk's form.
  const priorityHint = computed(() => {
    const priority = (priorities.data || []).find((row) => row.name === model.priority)
    return priority?.description?.trim() || undefined
  })

  // Site date formats reach the pickers as attrs; unset until the config arrives.
  function uiFor(row) {
    if (row.url_method) return { component: ApiOptionsField, props: { url: row.url_method } }
    if (!dateFormat.value) return undefined
    if (row.fieldtype === 'Datetime') return { props: { format: `${dateFormat.value} ${timeFormat.value}` } }
    if (row.fieldtype === 'Date') return { props: { format: dateFormat.value } }
  }

  // FormLayout resolves the depends_on rules itself against the values typed so far.
  const fields = computed(() =>
    (template.data?.fields || []).map((row) => ({
      fieldname: row.fieldname,
      fieldtype: row.fieldtype,
      label: __(row.label),
      options: row.options,
      reqd: Boolean(row.required),
      placeholder: row.placeholder || undefined,
      description: row.fieldname === 'priority' ? priorityHint.value : undefined,
      dependsOn: row.depends_on,
      mandatoryDependsOn: row.mandatory_depends_on,
      filters: row.link_filters ? parseLinkFilters(row.link_filters) : undefined,
      readOnly: Boolean(row.disabled),
      ui: { ...uiFor(row), on: scriptListeners(row) },
    })),
  )

  const layout = computed(() => [
    {
      sections: [
        {
          hideLabel: true,
          hideBorder: true,
          columns: [
            { fields: fields.value.filter((_, index) => index % 2 === 0) },
            { fields: fields.value.filter((_, index) => index % 2 === 1) },
          ],
        },
      ],
    },
  ])

  const canSubmit = computed(() => {
    if (!subject.value || isContentEmpty(description.value)) return false
    return fields.value
      .filter((field) => evaluateDependsOn(field.dependsOn, model))
      .filter((field) => field.reqd || (field.mandatoryDependsOn && evaluateDependsOn(field.mandatoryDependsOn, model)))
      .every((field) => model[field.fieldname])
  })

  function createTicket() {
    if (!canSubmit.value) return
    // The dialog's "Web link" source stores a URL without a File doc, which the server cannot link.
    const uploaded = attachments.value.map((file) => uploadedByUrl.get(file.file_url))
    if (uploaded.includes(undefined)) {
      return toast.error(__('Web links cannot be attached; upload the file instead'))
    }
    return runAction(
      async () => {
        const ticket = await newTicket.submit({
          doc: {
            subject: subject.value,
            description: description.value,
            template: DEFAULT_TEMPLATE,
            ...model,
          },
          attachments: uploaded,
        })
        navigateTo(ROUTES.ticket(ticket.name))
      },
      { busy: isCreating, fallback: __('Could not create the ticket') },
    )
  }

  return {
    ...session,
    customActions,
    about,
    fields,
    layout,
    model,
    setDescription,
    canSubmit,
    attachments,
    uploadPrivately,
    isCreating,
    createTicket,
  }
}
