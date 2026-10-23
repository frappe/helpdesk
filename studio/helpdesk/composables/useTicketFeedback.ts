import { computed, ref, watch } from 'vue'
import { createListResource } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { CLOSED_STATUS } from '@app/stores/ticketMeta'

// Well past any real count per rating.
const FEEDBACK_OPTION_LIMIT = 100

export function useTicketFeedback(saveTicket) {
  const isFeedbackOpen = ref(false)
  // Stars, as Rating counts; HD Ticket stores a fraction.
  const feedbackStars = ref(0)
  const feedbackOption = ref<string | null>(null)
  const feedbackText = ref('')
  const isFeedbackSaving = ref(false)

  const options = createListResource({
    doctype: 'HD Ticket Feedback Option',
    fields: ['name', 'label'],
    pageLength: FEEDBACK_OPTION_LIMIT,
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

  function openFeedback() {
    isFeedbackOpen.value = true
  }

  function selectFeedbackOption(name: string) {
    feedbackOption.value = name
  }

  // Status saved with the rating: `validate_feedback` refuses a close without one.
  async function submitFeedback() {
    if (!feedbackOption.value) return
    const saved = await saveTicket(
      { status: CLOSED_STATUS, feedback: feedbackOption.value, feedback_extra: feedbackText.value },
      { busy: isFeedbackSaving, fallback: __('Could not save the feedback') },
    )
    if (saved) isFeedbackOpen.value = false
  }

  return {
    isFeedbackOpen,
    openFeedback,
    feedbackStars,
    feedbackOptions,
    selectFeedbackOption,
    feedbackText,
    isFeedbackSaving,
    canSubmitFeedback: computed(() => Boolean(feedbackOption.value)),
    submitFeedback,
  }
}
