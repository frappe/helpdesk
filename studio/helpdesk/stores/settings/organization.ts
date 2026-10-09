import { ref, computed, watch } from 'vue'
import { call, toast } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { askConfirm, countLabel, errorMessage } from '@app/utils'
import { ROLES } from './roles'

const API = 'helpdesk.api.organization'

export function createOrganizationSettings(core) {
  const selectedOrganizationName = ref(null)
  const organization = ref(null)

  const isManager = computed(() => Boolean(organization.value?.is_manager))
  const canInvite = computed(() => Boolean(organization.value?.can_invite))
  const canChangeRoles = computed(() => Boolean(organization.value?.can_change_roles))
  const canRemoveMembers = computed(() => Boolean(organization.value?.can_remove_members))
  const canEdit = computed(() => Boolean(organization.value?.can_edit))
  const members = computed(() => organization.value?.members || [])
  const canLeaveOrganization = computed(() => core.organizations.value.length > 1)
  const invites = computed(() => organization.value?.invites || [])

  const managesAnyOrganization = computed(() =>
    core.organizations.value.some((row) => row.role !== 'Member'),
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
    isManager.value
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
  const inviteRole = ref<'Member' | 'Manager'>('Member')
  const inviteContacts = ref([])

  core.afterLoad(() => {
    if (selectedOrganizationName.value) return loadOrganization(selectedOrganizationName.value)
  })

  function callOrganization(method: string, args: Record<string, unknown> = {}) {
    return call(`${API}.${method}`, { customer: selectedOrganizationName.value, ...args })
  }

  async function loadOrganization(name) {
    try {
      organization.value = await call(`${API}.get_organization`, { customer: name })
    } catch (error) {
      console.error(error)
      toast.error(errorMessage(error, __('Could not open organization')))
      closeOrganization()
    }
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

  // A list of one is not a choice, however the reader reached the screen.
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

  // Watched, not fetched in `openInvite`: the URL hash opens the form without going through it.
  watch(inviteOpen, (open) => open && loadInvitableContacts())

  async function loadInvitableContacts() {
    inviteContacts.value = []
    try {
      inviteContacts.value = await callOrganization('get_invitable_contacts')
    } catch (error) {
      console.error(error)
    }
  }

  function sendInvite() {
    const emails = inviteEmails.value.map((email) => email.trim()).filter(Boolean)
    if (!emails.length) return toast.error(__('Please enter an email address'))
    const pending = new Set(invites.value.map((invite) => invite.email))
    return core.run(
      async () => {
        await callOrganization('invite_members', { emails, role: ROLES[inviteRole.value].role })
        closeInvite()
      },
      countLabel(emails.length, __('Invitation sent'), __('Invitations sent')),
      () => {
        if (emails.some((email) => pending.has(email))) return null
        if (!emails.every((email) => invites.value.some((invite) => invite.email === email))) return null
        closeInvite()
        return countLabel(
          emails.length,
          __('Invitation created, but the email could not be sent'),
          __('Invitations created, but the emails could not be sent'),
        )
      },
    )
  }

  function confirmAndRun(dialog, request, successMessage, landed?) {
    askConfirm({ ...dialog, action: () => core.run(request, successMessage, landed) })
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

  function cancelInvitation(invite) {
    confirmAndRun(
      {
        title: __('Cancel invitation'),
        message: __('The invitation sent to {0} will no longer be usable.', [invite.email]),
        label: __('Cancel invitation'),
        theme: 'red',
      },
      () => callOrganization('cancel_invitation', { invitation: invite.invitation }),
      __('Invitation cancelled'),
      () =>
        invites.value.every((row) => row.invitation !== invite.invitation) &&
        __('Invitation cancelled, but the notice could not be emailed'),
    )
  }

  function updateOrganizationImage(image: string, successMessage: string) {
    return core.run(() => callOrganization('update_organization_image', { image }), successMessage)
  }

  function uploadOrganizationImage() {
    core.pickImage((fileUrl) => updateOrganizationImage(fileUrl, __('Logo updated')))
  }

  function removeOrganizationImage() {
    return updateOrganizationImage('', __('Logo removed'))
  }

  return {
    // Bound by the blocks under these names.
    selectedOrganization: selectedOrganizationName,
    settingsOrganization: organization,
    canLeaveOrganization,
    canInvite,
    canChangeRoles,
    canRemoveMembers,
    showLastSeen: isManager,
    canEdit,
    organizationMembers: members,
    organizationInvites: invites,
    organizationScreenTitle,
    organizationScreenDescription,
    organizationDetailDescription,
    organizationTab,
    organizationTabOptions,
    inviteOpen,
    inviteEmails,
    inviteRole,
    inviteContacts,
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
