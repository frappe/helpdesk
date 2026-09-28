import { computed, ref, watch } from 'vue'
import { createListResource } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { CLOSED_STATUS } from '@app/stores/ticketMeta'
import { runAction, updateTicket } from '@app/utils'

export function useTicketFeedback(ticket) {
  const isFeedbackOpen = ref(false)
  const transition = ref<Record<string, string>>({})
  // In stars, the way the Rating component counts; HD Ticket stores a fraction.
  const feedbackStars = ref(0)
  const feedbackOption = ref<string | null>(null)
  const feedbackText = ref('')
  const isFeedbackSaving = ref(false)

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

  watch(feedbackStars, (stars) => {
    resetFeedbackAnswer()
    options.update({ filters: { rating: stars / 5, disabled: 0 } })
    options.reload()
  })

  watch(isFeedbackOpen, (open) => {
    if (open) return
    feedbackStars.value = 0
    resetFeedbackAnswer()
  })

  function resetFeedbackAnswer() {
    feedbackOption.value = null
    feedbackText.value = ''
  }

  // `validate_feedback` blocks a non-agent from the Resolved category without a rating.
  function openFeedback(status = CLOSED_STATUS) {
    transition.value = { status }
    isFeedbackOpen.value = true
  }

  function closeFeedback() {
    isFeedbackOpen.value = false
  }

  function selectFeedbackOption(name: string) {
    feedbackOption.value = name
  }

  function submitFeedback() {
    if (!feedbackOption.value) return
    return runAction(
      async () => {
        await updateTicket(ticket.data.name, {
          ...transition.value,
          ...(ticket.data.feedback
            ? {}
            : { feedback: feedbackOption.value, feedback_extra: feedbackText.value }),
        })
        closeFeedback()
        ticket.fetch()
      },
      { busy: isFeedbackSaving, fallback: __('Could not save the feedback') },
    )
  }

  return {
    isFeedbackOpen,
    openFeedback,
    closeFeedback,
    feedbackStars,
    feedbackOptions,
    feedbackOption,
    selectFeedbackOption,
    feedbackText,
    isFeedbackSaving,
    canSubmitFeedback: computed(() => Boolean(feedbackOption.value)),
    submitFeedback,
  }
}
