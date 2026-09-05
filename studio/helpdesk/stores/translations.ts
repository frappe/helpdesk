import { ref } from 'vue'
import { createResource } from 'frappe-ui'

// The same translations the agent portal reads: `helpdesk.api.general.get_translations`
// serves the .po-backed map for the session's language (System Settings' language for a
// guest — the endpoint is allow_guest). A Studio page renders its text straight from the
// block tree with no `__()` between the two, so the portal fetches the map itself and
// `t()` looks strings up at bind time. A string the .po files don't carry yet falls back
// to the English it was written in, exactly as `__()` does in the desk.

const words = ref<Record<string, string>>({})

// GET, as the endpoint requires — and cached under the same key the desk uses, so
// the two portals in one browser share the download.
const translations = createResource({
  url: 'helpdesk.api.general.get_translations',
  method: 'GET',
  cache: 'translations',
  auto: true,
  onSuccess: (data) => (words.value = data || {}),
})

function loadTranslations() {
  translations.reload()
}

/** What the reader chose — `hi-IN` and `hi` both read as Hindi.
 *
 *  A ref rather than a read of the cookie each time, so choosing a language can swap the
 *  portal's words in place. Every string goes through `t()` inside a computed, so setting
 *  this re-renders them all — which is what saves the settings dialog from reloading the
 *  page, and the reader from watching it blank out and come back. */
export const language = ref(readLanguage().split('-')[0])

/** Told to the portal when the reader picks a new one. The server answers
 *  `get_translations` from the User's saved language, so this refetches once the
 *  preference has been written. */
export function setLanguage(value: string) {
  language.value = (value || 'en').split('-')[0]
  loadTranslations()
}

function readLanguage() {
  const cookie = document.cookie
    .split('; ')
    .find((entry) => entry.startsWith('user_lang='))
  return decodeURIComponent(cookie?.split('=')[1] || '') || document.documentElement.lang || 'en'
}

/** The server's translation for this string, or the English it was written in. */
export function t(text: string) {
  return words.value[text] || text
}

/** "Assigned to Rosa Mendez" — the phrase is translated, the name is not. */
export function tFormat(text: string, value: string) {
  return `${t(text)} ${value}`.trim()
}
