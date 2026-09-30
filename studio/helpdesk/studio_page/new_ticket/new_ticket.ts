import { computed, reactive, ref, watch } from 'vue'
import { createListResource, toast, useFileUpload } from 'frappe-ui'
import { evaluateDependsOn } from '@framework/ui/FormLayout'
import { __ } from '@helpdesk/shared/translation'
import { isContentEmpty, parseLinkFilters } from '@helpdesk/shared/utils'
import ApiOptionsField from '@app/components/common/ApiOptionsField.vue'
import { ROUTES } from '@app/routes'
import { navigateTo } from '@app/stores/router'
import { useSettingsModal } from '@app/stores/settings'
import { runAction } from '@app/utils'

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
    (template.data?.fields || [])
      .filter((row) => !row.hide_from_customer)
      .map((row) => ({
        fieldname: row.fieldname,
        fieldtype: row.fieldtype,
        label: row.label,
        options: row.options,
        reqd: Boolean(row.required),
        placeholder: row.placeholder || undefined,
        description: row.fieldname === 'priority' ? priorityHint.value : undefined,
        dependsOn: row.depends_on,
        mandatoryDependsOn: row.mandatory_depends_on,
        filters: row.link_filters ? parseLinkFilters(row.link_filters) : undefined,
        ui: uiFor(row),
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
        await newTicket.submit({
          doc: {
            subject: subject.value,
            description: description.value,
            template: DEFAULT_TEMPLATE,
            ...model,
          },
          attachments: uploaded,
        })
        navigateTo(ROUTES.ticketList)
      },
      { fallback: __('Could not create the ticket') },
    )
  }

  return {
    ...session,
    about,
    fields,
    layout,
    model,
    setDescription,
    canSubmit,
    attachments,
    uploadPrivately,
    createTicket,
  }
}
