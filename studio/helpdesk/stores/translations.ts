import { ref } from 'vue'
import { createResource } from 'frappe-ui'

// A Studio page renders text straight from the block tree with no `__()` between the two,
// so the portal fetches the map itself and `t()` looks strings up at bind time.

const words = ref<Record<string, string>>({})

// Cached under the desk's key, so two portals in one browser share the download.
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

// A ref, not a cookie read, so setting it re-renders every `t()` in place of a reload.
export const language = ref(readLanguage().split('-')[0])

// The server answers from the User's saved language, so refetch once that is written.
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

export function t(text: string) {
  return words.value[text] || text
}

// The phrase is translated, the name is not.
export function tFormat(text: string, value: string) {
  return `${t(text)} ${value}`.trim()
}
