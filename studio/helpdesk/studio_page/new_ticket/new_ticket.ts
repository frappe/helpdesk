import { reactive, computed, ref, watch } from 'vue'
import { toast } from 'frappe-ui'
import { useSettingsModal } from '@app/stores/settings'

// New ticket form. The middle fields render through a Repeater over the HD Ticket
// Template's field list (`fields`); each repeated FormControl reads its value with
// `{{ getField(dataItem.fieldname) }}` and writes back via an `update:modelValue`
// Run-Script calling `setField`. The suggested-articles card is a separate custom
// component (KbArticleSuggestions.vue) fed the subject variable as `query`.
export default function setup(context) {
  const { subject, description, template, ticketTypes, newTicket, router, route } = context
  const { guestName, guestEmail, guestTicket } = context
  const session = useSettingsModal(context)

  // Arriving from the help page: whatever was searched for becomes the subject, so
  // nobody retypes it — and it immediately feeds the suggested-articles card.
  const searched = String(route?.query?.subject || '').trim()
  if (searched && !subject.value) subject.value = searched

  // The template and its ticket types are permission-gated, so they are fetched once
  // the session is known rather than on mount — a guest asking for them only 403s.
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
    if (session.isGuest.value) return isEmail(guestEmail.value)
    return fields.value.filter((f) => f.required).every((f) => model[f.fieldname])
  })

  function isEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || '').trim())
  }

  // Set once the ticket exists, which is also what swaps the form for the receipt.
  const submittedTicket = ref(null)

  // What to say about getting back to it. A visitor has no account, so the way back is
  // the invitation the server just sent — unless the address already had one.
  const submittedMessage = computed(() => {
    const ticket = submittedTicket.value
    if (!ticket) return ''
    const email = ticket.email || ''
    if (ticket.invite === 'has_account')
      return `We'll reply to ${email}. Sign in to follow it.`
    if (ticket.invite === 'pending')
      return `We'll reply to ${email}. Open the invitation already sent there to follow it.`
    return `We've emailed ${email} — open it to set a password and follow this ticket.`
  })

  // Only somebody who can already sign in is offered the sign-in.
  const submittedSignInUrl = computed(() =>
    submittedTicket.value?.invite === 'has_account'
      ? `/login?redirect-to=/kb/tickets/${submittedTicket.value.name}`
      : '',
  )

  function goToSignIn() {
    if (submittedSignInUrl.value) window.location.href = submittedSignInUrl.value
  }

  function createTicket() {
    if (!canSubmit.value) return
    const request = session.isGuest.value ? raiseAsGuest() : raiseAsCustomer()
    request.catch((error) => toast.error(error?.messages?.[0] || 'Could not create the ticket'))
  }

  // A visitor has nowhere to be sent afterwards — no ticket list, no account — so the
  // page keeps them here and tells them what happened.
  function raiseAsGuest() {
    return guestTicket
      .submit({
        subject: subject.value,
        description: description.value,
        email: guestEmail.value.trim(),
        first_name: guestName.value.trim(),
      })
      .then((created) => (submittedTicket.value = created))
  }

  function raiseAsCustomer() {
    return newTicket
      .submit({
        doc: { subject: subject.value, description: description.value, template: 'Default', ...model },
        attachments: attachments.value,
      })
      .then(() => router.push('/customer-tickets'))
  }

  return {
    ...session,
    fields, getField, setField, setDescription, controlType, optionsFor, canSubmit,
    attachments, setAttachments,
    createTicket, submittedTicket, submittedMessage, submittedSignInUrl, goToSignIn,
  }
}
