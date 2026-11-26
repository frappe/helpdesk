import { computed } from 'vue'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'

export default function setup(context) {
  const question = computed(() => String(context.route?.query?.q ?? '').trim())
  return { ...useKnowledgeBaseHeader(context), question }
}
