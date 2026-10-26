import { useStorage } from '@vueuse/core'

// Apart from the settings store, so the desk's new-ticket form can import it.
export const conversationLayout = useStorage('kb:conversation-layout', 'timeline')
