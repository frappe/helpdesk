import { computed, effectScope, ref, watch } from 'vue'
import { readKnowledgeBasePreview } from '@helpdesk/shared/knowledgeBasePreview'
import { isSafeLink } from '@helpdesk/shared/utils'
import { useSession } from '@app/stores/session'
import { accountMenuOptions, useSettingsModal } from '@app/stores/settings'
import { runFormScripts } from '@app/utils'

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
  customActions.value = await runFormScripts(data, scriptContext)
  // Settings' Preview shows its unsaved quick links in place of the saved ones, until a save clears it.
  headerLinks.value = (readKnowledgeBasePreview()?.links || data._customLinks || [])
    .filter((link) => link?.label && isSafeLink(link.url))
    .map((link) => ({ ...link, icon: serviceIcon(link.url) }))
}

// Runs the "Apply to knowledge base" form scripts; only the knowledge base pages use this header.
// Returns the settings, with this header's actions, links and menu in place of theirs.
export function useKnowledgeBaseHeader(context) {
  if (!scriptContext) {
    // Not the whole context: the first page's resources would outlive it.
    scriptContext = { call: context.call, router: context.router }
    // Detached from the page so scripts run once a visit, and again only when the list changes.
    effectScope(true).run(() =>
      watch(
        () => JSON.stringify(session.config.value?.knowledge_base_form_scripts || []),
        (scripts) => runScripts(JSON.parse(scripts)),
        { immediate: true },
      ),
    )
  }
  return { ...useSettingsModal(context), customActions, headerLinks, accountMenuOptions: menuOptions }
}
