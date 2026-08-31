import { ref, computed, watch, nextTick } from 'vue'
import { call, toast, FileUploadHandler, useTheme } from 'frappe-ui'
import { usePreferences } from '@app/stores/preferences'
import { useSession } from '@app/stores/session'
import { t } from '@app/stores/translations'

// Shared state + actions for the portal settings dialog, used by every page script
// via `useSettingsModal(context)`. The dialog itself is the `kb_settings` studio
// component, which binds to whatever the host page's script returns — so every page
// carrying it returns this store. Backed by helpdesk.api.organization.

const MANAGER_ROLE = 'HD Customer Manager'
const MEMBER_ROLE = 'HD Customer'
const HASH_ROOT = 'settings'

// One instance for the whole app: per-call state would give each page a private copy,
// so a load on one would leave the others showing stale settings.
const store = createSettingsStore()

// Every page script imports this module, so calling it here applies the saved theme on
// load rather than only once the settings dialog renders the picker.
const { currentTheme, setTheme } = useTheme()

// Writable so the theme Select can bind to it two-way; frappe-ui persists the choice.
const theme = computed({
  get: () => currentTheme.value,
  set: setTheme,
})

// Every page script goes through here, so the session store rides along rather than
// being wired into each one: the topbar it feeds is on every page too.
export function useSettingsModal(context) {
  if (context) store.bindRouter(context.router)
  return { ...store, ...usePreferences(), ...useSession(context), theme }
}

function createSettingsStore() {
  const settingsOpen = ref(false)
  const settingsTab = ref('profile') // 'profile' | 'members' | 'organization'
  const settingsData = ref(null)
  const settingsBusy = ref(false)

  // A contact can belong to several organizations, so the modal lists them and
  // drills into one at a time. `selectedOrg` null means the list is showing.
  const selectedOrg = ref(null)
  const orgDetail = ref(null)

  const settingsUser = computed(() => settingsData.value?.user || {})
  const organizations = computed(() => settingsData.value?.organizations || [])
  const settingsOrg = computed(() => orgDetail.value)
  const isOrgManager = computed(() => Boolean(orgDetail.value?.is_manager))
  const isAgentUser = computed(() => Boolean(settingsData.value?.is_agent))
  const orgMembers = computed(() => orgDetail.value?.members || [])

  // A plain member of every organization they belong to can open one and read it, but
  // change nothing in it — so the screen says what it will actually let them do.
  const managesAnyOrg = computed(() =>
    organizations.value.some((org) => org.role !== 'Member'),
  )
  const organizationScreenTitle = computed(() =>
    t(managesAnyOrg.value ? 'Manage organization' : 'View organization'),
  )
  const organizationScreenDescription = computed(() =>
    t(
      managesAnyOrg.value
        ? 'Pick an organization to manage its people and settings.'
        : 'Pick an organization to see its people and settings.',
    ),
  )

  // Managing an organization takes two yeses: you manage *this* one, and the helpdesk
  // allows customer-side self-service at all (HD Settings, off by default — most
  // helpdesks keep user administration agent-side). The server enforces both
  // independently; these only decide whether the controls are worth drawing.
  const portalConfig = computed(() => useSession().config.value || {})
  const canManageMembers = computed(() =>
    Boolean(isOrgManager.value && portalConfig.value.allow_customer_managers_to_invite),
  )
  const canEditOrganization = computed(() =>
    Boolean(
      isOrgManager.value &&
        portalConfig.value.allow_customer_managers_to_edit_organization,
    ),
  )

  // Form state, seeded from the server payload on every load
  const profileFirstName = ref('')
  const profileLastName = ref('')
  const orgName = ref('')
  const inviteOpen = ref(false)
  const inviteEmails = ref([])
  const inviteRole = ref('Member') // 'Member' | 'Manager'
  const inviteContacts = ref([])
  const passwordOpen = ref(false)
  const currentPassword = ref('')
  const newPassword = ref('')

  // Destructive actions route through one dialog rather than window.confirm, the
  // way the agent portal's ConfirmDialog does.
  const confirmAction = ref(null)
  // Open state kept apart from the options, so what is on the dialog survives its own
  // closing animation. Clearing the options to close it meant every binding fell back to
  // its default on the way out — a role change, which asks in grey, turned red for the
  // length of the fade.
  const confirmOpen = ref(false)

  function askConfirm(options) {
    confirmAction.value = options
    confirmOpen.value = true
  }

  function cancelConfirm() {
    confirmOpen.value = false
  }

  function acceptConfirm() {
    confirmOpen.value = false
    return confirmAction.value?.action?.()
  }

  async function loadSettings() {
    try {
      settingsData.value = await call('helpdesk.api.organization.get_settings')
      profileFirstName.value = settingsUser.value.first_name || ''
      profileLastName.value = settingsUser.value.last_name || ''
      // By docname, not email: they differ for Administrator, and keying by email
      // loaded a different User doc — so language and timezone never took effect.
      usePreferences().loadPreferences(settingsUser.value.name)
      if (selectedOrg.value) await loadOrganization(selectedOrg.value)
    } catch (error) {
      console.error(error)
      toast.error('Could not load settings')
    }
  }

  // --- Organizations: list -> detail ---

  async function loadOrganization(name) {
    orgTab.value = 'members'
    try {
      orgDetail.value = await call('helpdesk.api.organization.get_organization', {
        customer: name,
      })
      orgName.value = orgDetail.value.customer_name || ''
    } catch (error) {
      console.error(error)
      toast.error(serverMessage(error) || 'Could not open organization')
      closeOrganization()
    }
  }

  function openOrganization(name) {
    selectedOrg.value = name
    orgDetail.value = null
    inviteOpen.value = false
    return loadOrganization(name)
  }

  // A list of one is not a choice. Whoever belongs to a single organization lands straight
  // in it, however they reached the screen — the nav item, a restored hash, or the list
  // arriving after the tab was already open.
  watch(
    [settingsTab, organizations],
    () => {
      if (settingsTab.value !== 'members' || selectedOrg.value) return
      if (organizations.value.length === 1) openOrganization(organizations.value[0].name)
    },
    { immediate: true },
  )

  function closeOrganization() {
    selectedOrg.value = null
    orgDetail.value = null
    inviteOpen.value = false
  }

  function openSettings(tab) {
    settingsTab.value = tab || 'profile'
    settingsOpen.value = true
    inviteOpen.value = false
    closeOrganization()
    loadSettings()
  }

  function closeSettings() {
    settingsOpen.value = false
  }

  // The dialog lives in the URL hash (#settings/<tab>[/<organization>[/invite]]) so it
  // layers over the page underneath and survives a refresh; the topbar menu opens it by
  // pushing that hash. Every screen the dialog can show gets its own segment, which is
  // what makes the device back button step back through them one at a time instead of
  // dismissing the whole dialog. Bound once per app, through `afterEach` rather than a
  // watcher on the route, because a page script's `route` is a snapshot taken when the
  // script ran.
  let routerBound = false
  // Held here rather than captured in the watch: every page hands over its own router
  // proxy, and the one the first page gave is tied to a component that has since gone —
  // writing the hash through it did nothing, so the URL stopped following the dialog.
  let router = null

  function bindRouter(value) {
    if (!value) return
    router = value
    if (routerBound) return
    routerBound = true
    applyHash(currentRoute().hash)
    router.afterEach((to) => applyHash(to.hash))
    watch([settingsOpen, settingsTab, selectedOrg, inviteOpen], () => pushHash())
  }

  // The router reaches a page script through a reactive proxy, which unwraps refs — so
  // `currentRoute` is the route itself there, and the ref only outside that proxy.
  function currentRoute() {
    return router?.currentRoute?.value || router?.currentRoute || {}
  }

  function applyHash(hash) {
    const [root, tab, ...rest] = readHash(hash).replace(/^#/, '').split('/')
    if (root !== HASH_ROOT) return closeSettings()
    if (settingsOpen.value) settingsTab.value = tab || 'profile'
    else openSettings(tab)
    const invite = rest[rest.length - 1] === 'invite'
    if (invite) rest.pop()
    // An organization is named by whatever is left, slashes and all.
    applyOrganizationHash(rest.join('/'), invite)
  }

  function applyOrganizationHash(org, invite) {
    if (!org) return closeOrganization()
    if (org !== selectedOrg.value) openOrganization(org)
    inviteOpen.value = invite
  }

  function settingsHash() {
    if (!settingsOpen.value) return ''
    const parts = [HASH_ROOT, settingsTab.value]
    if (selectedOrg.value) parts.push(selectedOrg.value)
    if (selectedOrg.value && inviteOpen.value) parts.push('invite')
    return `#${parts.join('/')}`
  }

  // Organization names carry spaces, which the router escapes on the way into the URL
  // and hands back escaped after a popstate — so every hash is read decoded, and the
  // ones we build stay unescaped and let the router do that job once.
  function readHash(hash) {
    try {
      return decodeURIComponent(String(hash || ''))
    } catch (error) {
      return String(hash || '')
    }
  }

  function pushHash() {
    if (!router) return
    const hash = settingsHash()
    const current = currentRoute()
    if (readHash(current.hash) === hash) return
    // Leaving a screen the way we came in unwinds history rather than growing it —
    // pushing the parent again would leave the device back button pointing forward,
    // into the very screen just closed.
    const previous = previousHash()
    if (previous !== null && readHash(previous) === hash) return router.back()
    // The path travels with it: a bare `{ hash }` resolves against whatever the router
    // thinks is current, which is not always the page the dialog is layered over.
    router.push({ path: current.path, query: current.query, hash })
  }

  // vue-router keeps the entry behind this one in history state, as a full path —
  // query and all — so only the part before the query names the page.
  function previousHash() {
    const previous = router?.options?.history?.state?.back
    if (typeof previous !== 'string') return null
    const index = previous.indexOf('#')
    const [location, hash] = index === -1 ? [previous, ''] : [previous.slice(0, index), previous.slice(index)]
    return location.split('?')[0] === currentRoute().path ? hash : null
  }

  /** `landed` is for actions that email as part of the same request: the notice is
   *  sent synchronously, so a mail failure fails the whole request even though the
   *  change is already saved. It re-checks the reloaded data and returns the wording
   *  for that case, or nothing if the action really did fail. */
  async function run(action, successMessage, landed) {
    if (settingsBusy.value) return
    settingsBusy.value = true
    try {
      await action()
      if (successMessage) toast.success(successMessage)
      await loadSettings()
    } catch (error) {
      console.error(error)
      await loadSettings()
      const partial = landed?.()
      if (partial) toast.warning(partial)
      else toast.error(serverMessage(error) || 'Something went wrong')
    } finally {
      settingsBusy.value = false
    }
  }

  function serverMessage(error) {
    return error?.messages?.[0] || error?.message
  }

  // --- Profile ---

  function saveProfile() {
    return run(
      () => call('helpdesk.api.organization.update_profile', {
        first_name: profileFirstName.value,
        last_name: profileLastName.value,
      }),
      'Profile updated'
    )
  }

  // The portal stores first and last name separately; the dialog edits one field, so it
  // splits on the first space and everything after it is the last name.
  function renameProfile(value) {
    const [first, ...rest] = value.split(/\s+/)
    profileFirstName.value = first
    profileLastName.value = rest.join(' ')
    return saveProfile()
  }

  function pickImage(onUploaded) {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    input.onchange = async () => {
      const file = input.files && input.files[0]
      if (!file) return
      try {
        const uploaded = await new FileUploadHandler().upload(file, { private: false, optimize: true })
        await onUploaded(uploaded.file_url)
      } catch (error) {
        console.error(error)
        toast.error('Could not upload image')
      }
    }
    input.click()
  }

  function uploadProfileImage() {
    pickImage((fileUrl) =>
      run(() => call('helpdesk.api.organization.update_profile', { image: fileUrl }), 'Photo updated')
    )
  }

  function removeProfileImage() {
    return run(() => call('helpdesk.api.organization.update_profile', { image: '' }), 'Photo removed')
  }

  // --- Password ---

  function openPasswordChange() {
    currentPassword.value = ''
    newPassword.value = ''
    passwordOpen.value = true
  }

  function changePassword() {
    if (!currentPassword.value || !newPassword.value) {
      toast.error('Please fill in both passwords')
      return
    }
    return run(async () => {
      await call('frappe.core.doctype.user.user.update_password', {
        old_password: currentPassword.value,
        new_password: newPassword.value,
      })
      passwordOpen.value = false
    }, 'Password updated')
  }

  // --- Manage organization ---

  // Inviting is its own screen inside the organization panel, the same way the
  // organization list drills into a detail — not a dialog on top of it.
  function openInvite() {
    inviteEmails.value = []
    inviteRole.value = 'Member'
    inviteOpen.value = true
  }

  // Watched rather than fetched in `openInvite`: the screen is also reachable
  // straight from the URL hash, which sets the flag without going through it.
  watch(inviteOpen, (open) => open && loadInvitableContacts())

  // Fetched once per visit rather than per keystroke: the list is only this
  // organization's own domain, so the input filters it in place.
  async function loadInvitableContacts() {
    inviteContacts.value = []
    try {
      inviteContacts.value = await call(
        'helpdesk.api.organization.get_invitable_contacts',
        { customer: selectedOrg.value }
      )
    } catch (error) {
      console.error(error)
    }
  }

  function closeInvite() {
    inviteOpen.value = false
  }

  function sendInvite() {
    const emails = inviteEmails.value.map((email) => email.trim()).filter(Boolean)
    if (!emails.length) {
      toast.error('Please enter an email address')
      return
    }
    return run(async () => {
      const result = await call('frappe.core.api.user_invitation.invite_by_email', {
        emails: emails.join(','),
        roles: [inviteRole.value === 'Manager' ? MANAGER_ROLE : MEMBER_ROLE],
        redirect_to_path: '/helpdesk',
        app_name: 'helpdesk',
        customer: selectedOrg.value,
      })
      if (result.invited_emails?.length) {
        toast.success(result.invited_emails.length > 1 ? 'Invitations sent' : 'Invitation sent')
        inviteEmails.value = []
        inviteOpen.value = false
      } else if (result.pending_invite_emails?.length) {
        toast.error('An invitation for this email is already pending')
      } else if (result.accepted_invite_emails?.length) {
        toast.error('This person has already joined')
      } else if (result.disabled_user_emails?.length) {
        toast.error('This user account is disabled')
      }
    }, null, () => {
      if (!emails.every(isPendingMember)) return null
      inviteEmails.value = []
      inviteOpen.value = false
      return emails.length > 1
        ? 'Invitations created, but the emails could not be sent'
        : 'Invitation created, but the email could not be sent'
    })
  }

  function isPendingMember(email) {
    return orgMembers.value.some((member) => member.email === email && member.pending)
  }

  // A manager reads every ticket the organization has raised, not just their own,
  // so the change is spelled out before it is made — the same confirmation the agent
  // desk shows in ContactCard.updateManagerRole, worded the same way.
  function setMemberRole(member, role) {
    if (member.is_owner || member.pending) return
    const isManager = role === 'Manager'
    if (isManager === Boolean(member.is_manager)) return
    askConfirm({
      title: isManager ? 'Grant manager access' : 'Revoke manager access',
      message: isManager
        ? `${member.full_name} will get access to tickets raised by everyone in the organization.`
        : `${member.full_name} will only see their own tickets going forward.`,
      label: 'Confirm',
      // Not destructive either way, so it does not take the dialog's red default.
      theme: 'gray',
      action: () =>
        run(
          () => call('helpdesk.api.organization.update_member_role', {
            customer: selectedOrg.value,
            contact: member.contact,
            is_manager: isManager,
          }),
          'Role updated'
        ),
    })
  }

  function removeMember(member) {
    if (member.is_owner) return
    if (member.pending) return cancelInvitation(member)
    askConfirm({
      title: 'Remove member',
      message: `${member.full_name} will lose access to this organization's tickets.`,
      label: 'Remove',
      action: () =>
        run(
          () => call('helpdesk.api.organization.remove_member', {
            customer: selectedOrg.value,
            contact: member.contact,
          }),
          'Member removed'
        ),
    })
  }

  function cancelInvitation(member) {
    askConfirm({
      title: 'Cancel invitation',
      message: `The invitation sent to ${member.email} will no longer be usable.`,
      label: 'Cancel invitation',
      action: () =>
        run(
          () => call('helpdesk.api.organization.cancel_invitation', {
            customer: selectedOrg.value,
            invitation: member.invitation,
          }),
          'Invitation cancelled',
          () =>
            orgMembers.value.every((row) => row.invitation !== member.invitation) &&
            'Invitation cancelled, but the notice could not be emailed'
        ),
    })
  }

  // --- Organization settings ---

  function saveOrganization() {
    const name = orgName.value.trim()
    if (!name) {
      toast.error('Please enter an organization name')
      return
    }
    return run(
      async () => {
        // Renaming returns the new docname, which is also the drill-in key.
        const renamed = await call('helpdesk.api.organization.update_organization', {
          customer: selectedOrg.value,
          customer_name: name,
        })
        selectedOrg.value = renamed
      },
      'Organization updated'
    )
  }

  function renameOrganization(value) {
    orgName.value = value
    return saveOrganization()
  }

  // A Run Script handler calls functions rather than assigning to a binding, so the
  // fields the dialog toggles get one of these.
  function uploadOrgImage() {
    pickImage((fileUrl) =>
      run(() => call('helpdesk.api.organization.update_organization', {
        customer: selectedOrg.value,
        image: fileUrl,
      }), 'Logo updated')
    )
  }

  function removeOrgImage() {
    return run(() => call('helpdesk.api.organization.update_organization', {
      customer: selectedOrg.value,
      image: '',
    }), 'Logo removed')
  }

  // The portal's own furniture, in the reader's language. Here rather than on a page
  // because every page spreads this store, and the header is shared between them.
  // The theme picker's own options. In the block until now, which put three English
  // words inside a dialog that translates everything around them.
  // The organization panel has two things to say about a customer: who belongs to it, and
  // what they have raised lately. Tabs rather than one long scroll, since the second is a
  // list that grows.
  const orgTab = ref('members')
  const orgTabOptions = computed(() => [
    { label: t('Members'), value: 'members' },
    { label: t('Tickets'), value: 'tickets' },
  ])

  const themeOptions = computed(() => [
    { label: t('Light'), value: 'light' },
    { label: t('Dark'), value: 'dark' },
    { label: t('System'), value: 'system' },
  ])

  const words = computed(() => ({
    raiseTicket: t('Raise a ticket'),
    status: t('Status'),
    composerPrompt: t('Type a message'),
    solveAsk: t('Did this solve your issue?'),
    solveYes: t("Yes, it's fixed"),
    solveNo: t('No, still an issue'),
    feedbackTitle: t('Feedback Rating'),
  }))

  return {
    words,
    orgTab,
    orgTabOptions,
    themeOptions,
    // The settings dialog's own wording is bound through this rather than written into
    // the blocks, so the panel a reader opens to change their language is itself in it.
    t,
    settingsOpen,
    settingsTab,
    settingsBusy,
    settingsUser,
    organizations,
    // Pages that show organizations outside the dialog have to ask for them.
    loadSettings,
    selectedOrg,
    settingsOrg,
    isOrgManager,
    canManageMembers,
    canEditOrganization,
    isAgentUser,
    orgMembers,
    organizationScreenTitle,
    organizationScreenDescription,
    profileFirstName,
    profileLastName,
    orgName,
    inviteOpen,
    inviteEmails,
    inviteRole,
    inviteContacts,
    passwordOpen,
    currentPassword,
    newPassword,
    openPasswordChange,
    changePassword,
    bindRouter,
    openSettings,
    closeSettings,
    openOrganization,
    closeOrganization,
    confirmAction,
    confirmOpen,
    askConfirm,
    cancelConfirm,
    acceptConfirm,
    saveProfile,
    renameProfile,
    uploadProfileImage,
    removeProfileImage,
    openInvite,
    closeInvite,
    sendInvite,
    setMemberRole,
    removeMember,
    cancelInvitation,
    saveOrganization,
    renameOrganization,
    uploadOrgImage,
    removeOrgImage,
  }
}
