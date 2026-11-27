import { computed, effectScope, ref, watch } from 'vue'
import { ROUTES } from '@helpdesk/shared/portalRoutes'
import { readKnowledgeBasePreview } from '@helpdesk/shared/knowledgeBasePreview'
import { nestFooterRows } from '@helpdesk/shared/knowledgeBaseFooter'
import { isValidLink, runFormScripts } from '@helpdesk/shared/utils'
import { navigateTo } from '@app/stores/router'
import { useSession } from '@app/stores/session'
import { articleCountLabel } from '@app/stores/knowledgeBase'
import { accountMenuOptions, themeIcon, toggleTheme, useSettingsModal } from '@app/stores/settings'

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

// Empty hides the header button.
const pageActionLabel = computed(() =>
  session.canCreateTicket.value && !session.config.value?.hide_raise_ticket_button ? session.raiseTicketLabel.value : '',
)

const withIcons = (links) => links.filter(isValidLink).map((link) => ({ ...link, icon: serviceIcon(link.url) }))

const footer = computed(() => {
  const config = session.config.value
  if (!config?.show_footer) return null
  const { tagline, copyright, ...saved } = readKnowledgeBasePreview()?.footer || nestFooterRows(config)
  const columns = saved.columns
    .map((column) => ({ ...column, links: column.links.filter(isValidLink) }))
    .filter((column) => column.links.length)
  const socials = withIcons(saved.socials)
  return { tagline, copyright, columns, socials, isCompact: !columns.length }
})

// Phone: text links move into the logo menu.
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
  // Settings Preview shows unsaved links until saved.
  headerLinks.value = withIcons(readKnowledgeBasePreview()?.links || data._customLinks || [])
}

export function useKnowledgeBaseHeader(context) {
  if (!scriptContext) {
    // Not the whole context: the first page's resources would outlive it.
    scriptContext = { call: context.call, router: context.router }
    // Detached: run once per visit, again only when scripts change.
    effectScope(true).run(() =>
      watch(
        () => JSON.stringify(session.config.value?.knowledge_base_form_scripts || []),
        (scripts) => runScripts(JSON.parse(scripts)),
        { immediate: true },
      ),
    )
  }
  return {
    ...useSettingsModal(context),
    articleCountLabel,
    customActions,
    headerLinks,
    footer,
    accountMenuOptions: menuOptions,
    themeIcon,
    toggleTheme,
    pageActionLabel,
    pageActionIcon: 'lucide-plus',
    onPageAction: () => navigateTo(ROUTES.newTicket()),
  }
}
