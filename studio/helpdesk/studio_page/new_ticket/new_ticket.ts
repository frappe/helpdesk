import { computed, reactive, ref, watch } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { isContentEmpty } from '@helpdesk/shared/utils'
import { ROUTES } from '@app/routes'
import { navigateTo } from '@app/stores/router'
import { useSettingsModal } from '@app/stores/settings'
import { runAction } from '@app/utils'

const DEFAULT_TEMPLATE = 'Default'

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

// The template fields render through a Repeater: `getField` reads, `setField` writes via Run Script.
export default function setup(context) {
  const { subject, description, template, ticketTypes, newTicket, route } = context
  const session = useSettingsModal(context)

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

  const model = reactive({})

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
