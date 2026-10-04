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
import { useArticleSearch } from '@app/composables/useArticleSearch'

const DEFAULT_TEMPLATE = 'Default'
const UPLOAD_FOLDER = 'Home/Helpdesk'
const SUGGESTION_LIMIT = 3

export default function setup(context) {
  const { subject, description, template, newTicket, route } = context
  const settings = useSettingsModal(context)

  const searched = String(route?.query?.subject || '').trim()
  if (searched && !subject.value) subject.value = searched

  const model = reactive({})
  const attachments = ref([])

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

  const priorities = createListResource({
    doctype: 'HD Ticket Priority',
    fields: ['name', 'description'],
  })

  // Waits for the session: isGuest reads true until get_config answers.
  watch(
    settings.isGuest,
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

  const suggestions = useArticleSearch(subject, { limit: SUGGESTION_LIMIT })

  // TextEditor has no `modelValue`, so Studio's automatic binding never fires.
  function setDescription(html) {
    description.value = html
  }

  const dateFormat = computed(() => settings.config.value?.date_format?.toUpperCase())
  const timeFormat = computed(() => settings.config.value?.time_format)

  // As on the desk's form, only priority shows its description.
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
      ui: uiFor(row),
    })),
  )

  // Fields alternate between two columns, which would stack out of order on a phone.
  const layout = computed(() => [
    {
      sections: [
        {
          hideLabel: true,
          hideBorder: true,
          columns: settings.isPhone.value
            ? [{ fields: fields.value }]
            : [
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
      .filter((field) => evaluateDependsOn(field.dependsOn, model) && isRequired(field))
      .every((field) => model[field.fieldname])
  })

  function isRequired(field) {
    return field.reqd || (field.mandatoryDependsOn && evaluateDependsOn(field.mandatoryDependsOn, model))
  }

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
    ...settings,
    about,
    suggestions,
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
