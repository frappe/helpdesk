import { computed, ref, watch } from 'vue'
import { call, createListResource, toast } from 'frappe-ui'

// A port of `desk/src/pages/ticket/TicketFeedback.vue`; the dialog is Studio blocks.

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

  // `validate_feedback` blocks a non-agent from the Resolved category without a rating.
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

  // One write, so the rating and the transition can never disagree. The status written is
  // the one the opener asked for, never the one the ticket is already in.
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
