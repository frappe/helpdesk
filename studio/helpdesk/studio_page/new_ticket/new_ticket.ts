import { reactive, computed, ref, watch } from 'vue'
import { ROUTES } from '@app/routes'
import { toast } from 'frappe-ui'
import { useSettingsModal } from '@app/stores/settings'

// New ticket form. The middle fields render through a Repeater over the HD Ticket
// Template's field list (`fields`); each repeated FormControl reads its value with
// `{{ getField(dataItem.fieldname) }}` and writes back via an `update:modelValue`
// Run-Script calling `setField`.
export default function setup(context) {
  const { subject, description, template, ticketTypes, newTicket, router, route } = context
  const session = useSettingsModal(context)

  // Arriving from a search: whatever was searched for becomes the subject, so
  // nobody retypes it.
  const searched = String(route?.query?.subject || '').trim()
  if (searched && !subject.value) subject.value = searched

  // The template and its ticket types are permission-gated, so they are fetched once
  // the session is known rather than on mount — a guest asking for them only 403s
  // while being sent to the login page.
  watch(
    session.isGuest,
    (guest) => {
      if (guest) return
      template.fetch()
      ticketTypes.fetch()
    },
    { immediate: true }
  )

  // Values for the template-driven fields, keyed by fieldname.
  const model = reactive({})

  // File docs the attachment field has already uploaded. They ride along with the insert,
  // which is what `hd_ticket.api.new` does with its `attachments` argument.
  const attachments = ref([])
  const setAttachments = (files) => (attachments.value = files || [])

  const fields = computed(() =>
    (template.data?.fields || []).filter((f) => !f.hide_from_customer)
  )

  function getField(name) {
    return model[name] ?? ''
  }
  function setField(name, value) {
    model[name] = value
  }

  // TextEditor models `content` and emits `change` — it has no `modelValue`, so
  // Studio's automatic variable binding never fires and the description block
  // writes back through here instead.
  function setDescription(html) {
    description.value = html
  }

  function controlType(fieldtype) {
    if (fieldtype === 'Select') return 'select'
    if (fieldtype === 'Link') return 'autocomplete'
    return 'text'
  }

  function optionsFor(field) {
    if (field.fieldtype === 'Link') {
      return (ticketTypes.data || []).map((t) => ({ label: t.name, value: t.name }))
    }
    if (field.fieldtype === 'Select') {
      return (field.options || '')
        .split('\n')
        .map((o) => o.trim())
        .filter(Boolean)
        .map((o) => ({ label: o, value: o }))
    }
    return []
  }

  const canSubmit = computed(() => {
    const descEmpty = (description.value || '').replace(/<[^>]*>/g, '').trim().length === 0
    if (!subject.value || descEmpty) return false
    return fields.value.filter((f) => f.required).every((f) => model[f.fieldname])
  })

  function createTicket() {
    if (!canSubmit.value) return
    newTicket
      .submit({
        doc: { subject: subject.value, description: description.value, template: 'Default', ...model },
        attachments: attachments.value,
      })
      .then(() => router.push(ROUTES.ticketList))
      .catch((error) => toast.error(error?.messages?.[0] || 'Could not create the ticket'))
  }

  return {
    ...session,
    fields, getField, setField, setDescription, controlType, optionsFor, canSubmit,
    attachments, setAttachments,
    createTicket,
  }
}
