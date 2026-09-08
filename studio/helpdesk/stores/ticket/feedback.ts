import { computed, ref, watch } from 'vue'
import { call, createListResource, toast } from 'frappe-ui'

// The rating asked for before a ticket closes, when the helpdesk requires one —
// a port of `desk/src/pages/ticket/TicketFeedback.vue`, down to the rating-scoped
// option list and the single `set_value` that saves the feedback and the status
// together. The dialog itself is built from Studio blocks; this is its state.

export function useTicketFeedback(ticket) {
  const feedbackOpen = ref(false)
  // What the rating is saved alongside: the status the caller is heading for.
  const transition = ref<Record<string, string>>({})
  // In stars, the way the Rating component counts; HD Ticket stores a fraction.
  const feedbackStars = ref(0)
  const feedbackOption = ref<string | null>(null)
  const feedbackText = ref('')
  const feedbackSaving = ref(false)

  const options = createListResource({
    doctype: 'HD Ticket Feedback Option',
    fields: ['name', 'label'],
    pageLength: 99999,
  })

  const feedbackOptions = computed(() =>
    (options.data || []).map((option) => ({
      ...option,
      theme: feedbackOption.value === option.name ? 'blue' : 'gray',
    })),
  )

  // A different rating means a different option set, so the previous answer goes.
  watch(feedbackStars, (stars) => {
    feedbackOption.value = null
    feedbackText.value = ''
    options.update({ filters: { rating: stars / 5, disabled: 0 } })
    options.reload()
  })

  watch(feedbackOpen, (open) => {
    if (open) return
    feedbackStars.value = 0
    feedbackOption.value = null
    feedbackText.value = ''
  })

  // The status the caller is heading for. `validate_feedback` refuses to let a non-agent
  // enter the Resolved category without a rating, so on a helpdesk that requires feedback
  // the dialog's single save is the only way in — it carries the transition too.
  function openFeedback(status = 'Closed') {
    transition.value = { status }
    feedbackOpen.value = true
  }

  function closeFeedback() {
    feedbackOpen.value = false
  }

  function selectFeedbackOption(name: string) {
    feedbackOption.value = name
  }

  // One write, so the rating and the transition can never disagree — and so a helpdesk that
  // requires feedback can reach a settled status at all.
  //
  // The status written is the one the opener asked for, never the one the ticket is already
  // in: that is what keeps a rating from closing a ticket by itself. "Yes, it's fixed" asks
  // for Resolved and gets Resolved even on a ticket support already resolved; the topbar's
  // Close asks for Closed, and a Resolved ticket closes.
  //
  // A rating already given is never written over: the caller does not open this dialog on a
  // ticket that carries one, and if it is open when one lands, the transition still goes
  // through on its own.
  async function submitFeedback() {
    if (!feedbackOption.value || feedbackSaving.value) return
    feedbackSaving.value = true
    try {
      await call('frappe.client.set_value', {
        doctype: 'HD Ticket',
        name: ticket.data.name,
        fieldname: {
          ...transition.value,
          ...(ticket.data.feedback
            ? {}
            : {
                feedback: feedbackOption.value,
                feedback_extra: feedbackText.value,
              }),
        },
      })
      closeFeedback()
      ticket.fetch()
    } catch (error) {
      toast.error(error?.messages?.[0] || 'Could not save the feedback')
    } finally {
      feedbackSaving.value = false
    }
  }

  return {
    feedbackOpen,
    openFeedback,
    closeFeedback,
    feedbackStars,
    feedbackOptions,
    feedbackOption,
    selectFeedbackOption,
    feedbackText,
    feedbackSaving,
    canSubmitFeedback: computed(() => Boolean(feedbackOption.value)),
    submitFeedback,
  }
}
