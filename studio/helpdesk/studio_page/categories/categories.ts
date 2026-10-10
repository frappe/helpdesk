import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'

// Every category, for when the home page shows only the pinned ones.
export default function setup(context) {
  return useKnowledgeBaseHeader(context)
}
