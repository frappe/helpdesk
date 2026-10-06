import { computed, ref } from 'vue'
import { toast, useColorScheme } from 'frappe-ui'
import { createToast, setupCustomizations } from '@helpdesk/shared/formScripts'
import { useSession } from '@app/stores/session'
import { accountMenuOptions } from '@app/stores/settings'
import { scriptDialog } from '@app/utils'

const session = useSession()

const { resolvedColorScheme, toggleColorScheme } = useColorScheme()
const themeIcon = computed(() => (resolvedColorScheme.value === 'dark' ? 'lucide-sun' : 'lucide-moon-star'))

const headerLinks = computed(() => session.config.value?.header_links || [])

// On a phone the text links leave the header for the logo menu; service icons stay put.
const menuOptions = computed(() => [
  ...(session.isPhone.value ? headerLinks.value.filter((link) => !link.icon) : []).map((link) => ({
    icon: 'lucide-external-link',
    label: link.label,
    onClick: () =>
      link.open_in_new_tab ? window.open(link.url, '_blank', 'noopener') : (window.location.href = link.url),
  })),
  ...accountMenuOptions.value,
])

// Shared by every KB page, so a script runs once a visit: an announcement dialog does not reopen on each page.
const customActions = ref([])
let started = false

// The knowledge base header: the admin's links, and form scripts with "Apply to knowledge base",
// whose context is the ticket pages' minus the field helpers.
export function useKbHeader(context) {
  if (!started) {
    started = true
    session.loadSession().then(async () => {
      const data = { _form_script: session.config.value?.kb_form_scripts }
      await setupCustomizations(data, {
        call: context.call,
        router: context.router,
        toast,
        createToast,
        $dialog: scriptDialog,
      })
      customActions.value = data._customActions || []
    })
  }
  return { customActions, headerLinks, accountMenuOptions: menuOptions, themeIcon, toggleTheme: toggleColorScheme }
}
