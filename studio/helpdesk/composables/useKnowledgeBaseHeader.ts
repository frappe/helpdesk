import { computed, effectScope, ref, watch } from 'vue'
import { toast } from 'frappe-ui'
import { createToast, setupCustomizations } from '@helpdesk/shared/formScripts'
import { readKnowledgeBasePreview } from '@helpdesk/shared/knowledgeBasePreview'
import { isSafeLink } from '@helpdesk/shared/utils'
import { useSession } from '@app/stores/session'
import { accountMenuOptions } from '@app/stores/settings'
import { scriptDialog } from '@app/utils'

// A quick link to one of these shows as its icon, as on Frappe Wiki.
const SERVICE_ICONS = {
  'github.com': 'github',
  'youtube.com': 'youtube',
  'twitter.com': 'x',
  'x.com': 'x',
  'linkedin.com': 'linkedin',
  'discord.com': 'discord',
  'discord.gg': 'discord',
  'slack.com': 'slack',
  'facebook.com': 'facebook',
  'instagram.com': 'instagram',
  'reddit.com': 'reddit',
}

const session = useSession()

const customActions = ref([])
const headerLinks = ref([])

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

function serviceIcon(url: string) {
  const host = url.match(/^https?:\/\/(?:[^@/?#]*@)?([^/?#:]+)/i)?.[1].toLowerCase()
  if (!host) return null
  const domain = Object.keys(SERVICE_ICONS).find((domain) => host === domain || host.endsWith(`.${domain}`))
  return domain ? SERVICE_ICONS[domain] : null
}

let scriptContext = null

async function runScripts(scripts: string[]) {
  const data = { _form_script: scripts }
  await setupCustomizations(data, scriptContext)
  customActions.value = data._customActions || []
  // Settings' Preview shows its unsaved quick links in place of the saved ones, until a save clears it.
  headerLinks.value = (readKnowledgeBasePreview()?.links || data._customLinks || [])
    .filter((link) => link?.label && isSafeLink(link.url))
    .map((link) => ({ ...link, icon: serviceIcon(link.url) }))
}

// The knowledge base header: form scripts with "Apply to knowledge base", quick links among them,
// whose context is the ticket pages' minus the field helpers. Only the knowledge base pages spread
// this; the ticket pages keep their own actions and take the theme toggle from the settings store.
export function useKnowledgeBaseHeader(context) {
  if (!scriptContext) {
    scriptContext = { call: context.call, router: context.router, toast, createToast, $dialog: scriptDialog }
    // Detached from the page, so the scripts run once a visit: an announcement dialog does not reopen on each page.
    // They rerun when the list changes, as when quick links are saved.
    effectScope(true).run(() =>
      watch(
        () => JSON.stringify(session.config.value?.knowledge_base_form_scripts || []),
        (scripts) => runScripts(JSON.parse(scripts)),
        { immediate: true },
      ),
    )
  }
  return { customActions, headerLinks, accountMenuOptions: menuOptions }
}
