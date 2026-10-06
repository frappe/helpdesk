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

  const managesAnyOrganization = computed(() =>
    core.organizations.value.some((row) => row.role !== 'Member'),
  )
  const organizationScreenTitle = computed(() =>
    managesAnyOrganization.value ? __('Manage Organization') : __('View Organization'),
  )
  const organizationScreenDescription = computed(() =>
    managesAnyOrganization.value
      ? __('Pick an organization to manage its people and settings.')
      : __('Pick an organization to see its people and settings.'),
  )
  const organizationDetailDescription = computed(() =>
    isManager.value
      ? __("Manage your organization's members and tickets.")
      : __("View your organization's members and tickets."),
  )

  const orgTab = ref('members')
  const orgTabOptions = computed(() => [
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
    orgTab.value = 'members'
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
    return core.run(
      async () => {
        await callOrganization('invite_members', { emails, role: ROLES[inviteRole.value].role })
        closeInvite()
      },
      countLabel(emails.length, __('Invitation sent'), __('Invitations sent')),
      () => {
        if (!emails.every(isPendingMember)) return null
        closeInvite()
        return countLabel(
          emails.length,
          __('Invitation created, but the email could not be sent'),
          __('Invitations created, but the emails could not be sent'),
        )
      },
    )
  }

  function isPendingMember(email) {
    return members.value.some((member) => member.email === email && member.pending)
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
    if (member.pending) return cancelInvitation(member)
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

  function cancelInvitation(member) {
    confirmAndRun(
      {
        title: __('Cancel invitation'),
        message: __('The invitation sent to {0} will no longer be usable.', [member.email]),
        label: __('Cancel invitation'),
        theme: 'red',
      },
      () => callOrganization('remove_member', { invitation: member.invitation }),
      __('Invitation cancelled'),
      () =>
        members.value.every((row) => row.invitation !== member.invitation) &&
        __('Invitation cancelled, but the notice could not be emailed'),
    )
  }

  function updateOrganization(values, successMessage) {
    return core.run(async () => {
      // Renaming returns the new docname, which is also the drill-in key.
      selectedOrganizationName.value = await callOrganization('update_organization', values)
    }, successMessage)
  }

  function renameOrganization(value) {
    const name = value.trim()
    if (!name) return toast.error(__('Please enter an organization name'))
    return updateOrganization({ customer_name: name }, __('Organization updated'))
  }

  function uploadOrgImage() {
    core.pickImage((fileUrl) => updateOrganization({ image: fileUrl }, __('Logo updated')))
  }

  function removeOrgImage() {
    return updateOrganization({ image: '' }, __('Logo removed'))
  }

  return {
    // The blocks bind these two under their shorter names.
    selectedOrg: selectedOrganizationName,
    settingsOrg: organization,
    canLeaveOrganization,
    canInvite,
    canChangeRoles,
    canRemoveMembers,
    canEdit,
    orgMembers: members,
    organizationScreenTitle,
    organizationScreenDescription,
    organizationDetailDescription,
    orgTab,
    orgTabOptions,
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
    renameOrganization,
    uploadOrgImage,
    removeOrgImage,
  }
}
