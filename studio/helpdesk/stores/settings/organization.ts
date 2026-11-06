import { ref, computed, watch } from 'vue'
import { call, toast } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { askConfirm, countLabel, getErrorMessage } from '@helpdesk/shared/utils'
import { useSession } from '@app/stores/session'
import { ASSIGNABLE_ROLES, roleLabel, type RoleLabel } from './roles'
import { useRememberedCount } from '@app/composables/useRememberedCount'

const API = 'helpdesk.api.customer'

export function createOrganizationSettings(core) {
  const selectedOrganizationName = ref(null)
  const organization = ref(null)

  const { config } = useSession()

  const organizationCard = computed(() =>
    core.organizations.value.find((row) => row.name === selectedOrganizationName.value),
  )
  const settingsOrganization = computed(() => ({ ...organizationCard.value, ...organization.value }))

  const canManage = computed(() => Boolean(organizationCard.value && organizationCard.value.role !== 'Member'))
  const canInvite = computed(
    () => canManage.value && Boolean(config.value?.allow_customer_managers_to_invite),
  )
  const canManageOrganization = computed(
    () => canManage.value && Boolean(config.value?.allow_customer_managers_to_manage_organization),
  )
  const members = computed(() => organization.value?.members || [])
  const organizationLoading = computed(() => Boolean(selectedOrganizationName.value) && !organization.value)
  const canLeaveOrganization = computed(() => core.organizations.value.length > 1)
  const invitations = computed(() => organization.value?.invitations || [])

  const managesAnyOrganization = computed(() =>
    core.organizations.value.some((row) => row.role !== 'Member'),
  )
  // Loading shows a lone organization's screen, or the list, by last time's count.
  const organizationCountHint = useRememberedCount(
    'helpdesk-portal-organizations',
    // A failed load has no account: keep last time's count.
    () => (core.settingsLoaded.value && core.settingsUser.value.name ? core.organizations.value.length : undefined),
    1,
  )
  const organizationScreenTitle = computed(() =>
    managesAnyOrganization.value ? __('Manage Organization') : __('View Organization'),
  )
  const organizationScreenDescription = computed(() =>
    managesAnyOrganization.value
      ? __('Manage the organizations you belong to and their members.')
      : __('View the organizations you belong to and their members.'),
  )
  const organizationDetailDescription = computed(() =>
    canManage.value
      ? __("Manage your organization's members and tickets.")
      : __("View your organization's members and tickets."),
  )

  const organizationTab = ref('members')
  const organizationTabOptions = computed(() => [
    { label: __('Members'), value: 'members' },
    { label: __('Tickets'), value: 'tickets' },
  ])

  const inviteOpen = ref(false)
  const inviteEmails = ref([])
  const inviteRole = ref<RoleLabel>('Member')
  const inviteRoleOptions = computed(() => ASSIGNABLE_ROLES.map((role) => ({ label: roleLabel(role), value: role })))
  const inviteRoleDescription = computed(() =>
    inviteRole.value === 'Manager'
      ? __('Can see tickets raised by everyone in the organization.')
      : __('Can raise tickets and see their own tickets.'),
  )

  core.afterLoad(() => {
    if (selectedOrganizationName.value) return loadOrganization(selectedOrganizationName.value)
  })

  function searchInviteContacts(query: string) {
    return callOrganization('get_invitable_contacts', { query })
  }

  function callOrganization(method: string, args: Record<string, unknown> = {}) {
    return call(`${API}.${method}`, { customer: selectedOrganizationName.value, ...args })
  }

  async function loadOrganization(name) {
    try {
      const data = await call(`${API}.get_organization`, { customer: name })
      if (name === selectedOrganizationName.value) organization.value = data
    } catch (error) {
      if (name !== selectedOrganizationName.value) return
      console.error(error)
      getErrorMessage(error, true, __('Could not open organization'))
      closeOrganization()
    }
  }

  // Member changes don't touch the account.
  function reloadOrganization() {
    return loadOrganization(selectedOrganizationName.value)
  }

  function openOrganization(name) {
    selectedOrganizationName.value = name
    organization.value = null
    inviteOpen.value = false
    organizationTab.value = 'members'
    return loadOrganization(name)
  }

  function closeOrganization() {
    selectedOrganizationName.value = null
    organization.value = null
    inviteOpen.value = false
  }

  // A lone organization opens directly.
  watch(
    [core.settingsTab, core.organizations],
    () => {
      if (core.settingsTab.value !== 'members' || selectedOrganizationName.value) return
      if (core.organizations.value.length === 1) openOrganization(core.organizations.value[0].name)
    },
    { immediate: true },
  )

  function openInvite() {
    inviteEmails.value = []
    inviteRole.value = 'Member'
    inviteOpen.value = true
  }

  function closeInvite() {
    inviteEmails.value = []
    inviteOpen.value = false
  }

  function sendInvite() {
    const emails = inviteEmails.value.map((email) => email.trim()).filter(Boolean)
    if (!emails.length) return toast.error(__('Please enter an email address'))
    const pending = new Set(invitations.value.map((invitation) => invitation.email))
    return core.run(
      async () => {
        const result = await callOrganization('invite_members', { emails, is_manager: inviteRole.value === 'Manager' })
        closeInvite()
        const list = (emails: string[]) => emails.join(', ')
        if (result.invited_emails.length) toast.success(__('{0} invited successfully', list(result.invited_emails)))
        // The server hides why, so other organizations' people stay private.
        if (result.skipped_emails.length)
          toast.info(__('Could not invite {0}. They may already be a member or have a pending invite.', list(result.skipped_emails)))
        if (result.disabled_emails.length)
          toast.info(__('Could not invite {0}. Their account is disabled.', list(result.disabled_emails)))
      },
      null,
      () => {
        if (emails.some((email) => pending.has(email))) return null
        if (!emails.every((email) => invitations.value.some((invitation) => invitation.email === email))) return null
        closeInvite()
        return countLabel(
          emails.length,
          __('Invitation created, but the email could not be sent'),
          __('Invitations created, but the emails could not be sent'),
        )
      },
      reloadOrganization,
    )
  }

  function confirmAndRun(dialog, request, successMessage, landed?) {
    askConfirm({ ...dialog, action: () => core.run(request, successMessage, landed, reloadOrganization) })
  }

  function setMemberRole(member, role) {
    const makeManager = role === 'Manager'
    confirmAndRun(
      {
        title: makeManager ? __('Grant manager access') : __('Revoke manager access'),
        message: makeManager
          ? __('{0} will get access to tickets raised by everyone in the organization.', [member.full_name])
          : __('{0} will only see their own tickets going forward.', [member.full_name]),
        label: __('Confirm'),
      },
      () => callOrganization('update_member_role', { contact: member.contact, is_manager: makeManager }),
      __('Role updated'),
    )
  }

  function removeMember(member) {
    confirmAndRun(
      {
        title: __('Remove member'),
        message: __("{0} will lose access to this organization's tickets.", [member.full_name]),
        label: __('Remove'),
        theme: 'red',
      },
      () => callOrganization('remove_member', { contact: member.contact }),
      __('Member removed'),
    )
  }

  function cancelInvitation(invitation) {
    confirmAndRun(
      {
        title: __('Cancel invitation'),
        message: __('The invitation sent to {0} will no longer be usable.', [invitation.email]),
        label: __('Cancel invitation'),
        theme: 'red',
      },
      () => callOrganization('cancel_invitation', { invitation: invitation.name }),
      __('Invitation cancelled'),
      () =>
        invitations.value.every((row) => row.name !== invitation.name) &&
        __('Invitation cancelled, but the notice could not be emailed'),
    )
  }

  function updateOrganizationImage(image: string, successMessage: string) {
    return core.run(() => callOrganization('update_organization_image', { image }), successMessage)
  }

  function uploadOrganizationImage(fileUrl: string) {
    return updateOrganizationImage(fileUrl, __('Logo updated'))
  }

  function removeOrganizationImage() {
    return updateOrganizationImage('', __('Logo removed'))
  }

  return {
    // Bound by name from the blocks.
    selectedOrganization: selectedOrganizationName,
    settingsOrganization,
    canLeaveOrganization,
    canInvite,
    canManageOrganization,
    showLastActive: canManage,
    organizationMembers: members,
    organizationLoading,
    organizationInvitations: invitations,
    organizationScreenTitle,
    organizationCountHint,
    organizationScreenDescription,
    organizationDetailDescription,
    organizationTab,
    organizationTabOptions,
    inviteOpen,
    inviteEmails,
    inviteRole,
    inviteRoleOptions,
    inviteRoleDescription,
    searchInviteContacts,
    openOrganization,
    closeOrganization,
    openInvite,
    closeInvite,
    sendInvite,
    setMemberRole,
    removeMember,
    cancelInvitation,
    uploadOrganizationImage,
    removeOrganizationImage,
  }
}
