import { computed, reactive, ref, watch } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { isContentEmpty } from '@helpdesk/shared/utils'
import { ROUTES } from '@app/routes'
import { navigateTo } from '@app/stores/router'
import { useSettingsModal } from '@app/stores/settings'
import { runAction } from '@app/utils'

const DEFAULT_TEMPLATE = 'Default'

// How a template field renders and where its choices come from; anything else is text.
const FIELD_CONTROLS = {
  Select: {
    control: 'select',
    options: (field) => field.options.split('\n').map((option) => option.trim()).filter(Boolean),
  },
  Link: {
    control: 'autocomplete',
    options: (field, ticketTypes) => ticketTypes.map((ticketType) => ticketType.name),
  },
}

// The middle fields render through a Repeater over the template's field list, reading
// with `getField` and writing back through an `update:modelValue` Run Script.
export default function setup(context) {
  const { subject, description, template, ticketTypes, newTicket, route } = context
  const session = useSettingsModal(context)

  // Arriving from a search: what was searched for becomes the subject.
  const searched = String(route?.query?.subject || '').trim()
  if (searched && !subject.value) subject.value = searched

  // Permission-gated, so fetched once the session is known: a guest would only 403.
  watch(
    session.isGuest,
    (isGuest) => {
      if (isGuest) return
      template.fetch()
      ticketTypes.fetch()
    },
    { immediate: true },
  )

  // Values for the template-driven fields, keyed by fieldname.
  const model = reactive({})

  // Already uploaded; they ride along with the insert as `attachments`.
  const attachments = ref([])

  const fields = computed(() =>
    (template.data?.fields || []).filter((field) => !field.hide_from_customer),
  )

  function getField(name) {
    return model[name] ?? ''
  }

  function setField(name, value) {
    model[name] = value
  }

  // TextEditor has no `modelValue`, so Studio's automatic binding never fires.
  function setDescription(html) {
    description.value = html
  }

  function controlType(fieldtype) {
    return FIELD_CONTROLS[fieldtype]?.control || 'text'
  }

  function optionsFor(field) {
    const choices = FIELD_CONTROLS[field.fieldtype]?.options(field, ticketTypes.data || []) || []
    return choices.map((choice) => ({ label: choice, value: choice }))
  }

  const canSubmit = computed(() => {
    if (!subject.value || isContentEmpty(description.value)) return false
    return fields.value.filter((field) => field.required).every((field) => model[field.fieldname])
  })

  function createTicket() {
    if (!canSubmit.value) return
    return runAction(
      async () => {
        await newTicket.submit({
          doc: {
            subject: subject.value,
            description: description.value,
            template: DEFAULT_TEMPLATE,
            ...model,
          },
          attachments: attachments.value,
        })
        navigateTo(ROUTES.ticketList)
      },
      { fallback: __('Could not create the ticket') },
    )
  }

  return {
    ...session,
    fields,
    getField,
    setField,
    setDescription,
    controlType,
    optionsFor,
    canSubmit,
    attachments,
    createTicket,
  }
}
