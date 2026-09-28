import { ref, computed, watch } from 'vue'
import { call, toast } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { countLabel, errorMessage } from '@app/utils'
import { ROLES } from './roles'

// Backed by helpdesk.api.organization.
export function createOrganizationSettings(core) {
  // Null means the list is showing rather than one organization's detail.
  const selectedOrganizationName = ref(null)
  const organization = ref(null)

  const isManager = computed(() => Boolean(organization.value?.is_manager))
  const canInvite = computed(() => Boolean(organization.value?.can_invite))
  const canEdit = computed(() => Boolean(organization.value?.can_edit))
  const members = computed(() => organization.value?.members || [])

  // A plain member can read an organization but change nothing in it.
  const managesAnyOrganization = computed(() =>
    core.organizations.value.some((row) => row.role !== 'Member'),
  )
  const organizationScreenTitle = computed(() =>
    __(managesAnyOrganization.value ? 'Manage organization' : 'View organization'),
  )
  const organizationScreenDescription = computed(() =>
    __(
      managesAnyOrganization.value
        ? 'Pick an organization to manage its people and settings.'
        : 'Pick an organization to see its people and settings.',
    ),
  )
  const organizationDetailDescription = computed(() =>
    __(
      isManager.value
        ? "Manage your organization's members and tickets."
        : "View your organization's members and tickets.",
    ),
  )

  const orgTab = ref('members')
  const orgTabOptions = computed(() => [
    { label: __('Members'), value: 'members' },
    { label: __('Tickets'), value: 'tickets' },
  ])

  const inviteOpen = ref(false)
  const inviteEmails = ref([])
  const inviteRole = ref('Member') // 'Member' | 'Manager'
  const inviteContacts = ref([])

  core.afterLoad(() => {
    if (selectedOrganizationName.value) return loadOrganization(selectedOrganizationName.value)
  })

  async function loadOrganization(name) {
    orgTab.value = 'members'
    try {
      organization.value = await call('helpdesk.api.organization.get_organization', {
        customer: name,
      })
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
    return loadOrganization(name)
  }

  // A list of one is not a choice, however the reader reached the screen.
  watch(
    [core.settingsTab, core.organizations],
    () => {
      if (core.settingsTab.value !== 'members' || selectedOrganizationName.value) return
      if (core.organizations.value.length === 1)
        openOrganization(core.organizations.value[0].name)
    },
    { immediate: true },
  )

  // With one organization there is no list to go back to: the watch above drills straight in.
  const canLeaveOrganization = computed(() => core.organizations.value.length > 1)

  function closeOrganization() {
    selectedOrganizationName.value = null
    organization.value = null
    inviteOpen.value = false
  }

  function openInvite() {
    inviteEmails.value = []
    inviteRole.value = 'Member'
    inviteOpen.value = true
  }

  // Watched, not fetched in `openInvite`: the URL hash sets the flag without going through it.
  watch(inviteOpen, (open) => open && loadInvitableContacts())

  // Once per visit, not per keystroke: the input filters this list in place.
  async function loadInvitableContacts() {
    inviteContacts.value = []
    try {
      inviteContacts.value = await call('helpdesk.api.organization.get_invitable_contacts', {
        customer: selectedOrganizationName.value,
      })
    } catch (error) {
      console.error(error)
    }
  }

  function closeInvite() {
    inviteOpen.value = false
  }

  function sendInvite() {
    const emails = inviteEmails.value.map((email) => email.trim()).filter(Boolean)
    if (!emails.length) return toast.error(__('Please enter an email address'))
    return core.run(
      async () => {
        await call('helpdesk.api.organization.invite_members', {
          customer: selectedOrganizationName.value,
          emails,
          role: ROLES[inviteRole.value].role,
        })
        closeInviteForm()
      },
      countLabel(emails.length, 'Invitation sent', 'Invitations sent'),
      () => {
        if (!emails.every(isPendingMember)) return null
        closeInviteForm()
        return countLabel(
          emails.length,
          'Invitation created, but the email could not be sent',
          'Invitations created, but the emails could not be sent',
        )
      },
    )
  }

  function closeInviteForm() {
    inviteEmails.value = []
    inviteOpen.value = false
  }

  function isPendingMember(email) {
    return members.value.some((member) => member.email === email && member.pending)
  }

  // A manager reads every ticket the organization has raised, so the change is spelled out.
  function setMemberRole(member, role) {
    if (member.role === 'Owner' || member.pending || role === member.role) return
    const isManager = role === 'Manager'
    core.askConfirm({
      title: isManager ? __('Grant manager access') : __('Revoke manager access'),
      message: isManager
        ? __('{0} will get access to tickets raised by everyone in the organization.', [member.full_name])
        : __('{0} will only see their own tickets going forward.', [member.full_name]),
      label: __('Confirm'),
      // Not destructive either way, so it does not take the dialog's red default.
      theme: 'gray',
      action: () =>
        core.run(
          () =>
            call('helpdesk.api.organization.update_member_role', {
              customer: selectedOrganizationName.value,
              contact: member.contact,
              is_manager: isManager,
            }),
          __('Role updated'),
        ),
    })
  }

  function removeMember(member) {
    if (member.role === 'Owner') return
    if (member.pending) return cancelInvitation(member)
    core.askConfirm({
      title: __('Remove member'),
      message: __("{0} will lose access to this organization's tickets.", [member.full_name]),
      label: __('Remove'),
      action: () =>
        core.run(
          () =>
            call('helpdesk.api.organization.remove_member', {
              customer: selectedOrganizationName.value,
              contact: member.contact,
            }),
          __('Member removed'),
        ),
    })
  }

  function cancelInvitation(member) {
    core.askConfirm({
      title: __('Cancel invitation'),
      message: __('The invitation sent to {0} will no longer be usable.', [member.email]),
      label: __('Cancel invitation'),
      action: () =>
        core.run(
          () =>
            call('helpdesk.api.organization.remove_member', {
              customer: selectedOrganizationName.value,
              invitation: member.invitation,
            }),
          __('Invitation cancelled'),
          () =>
            members.value.every((row) => row.invitation !== member.invitation) &&
            __('Invitation cancelled, but the notice could not be emailed'),
        ),
    })
  }

  function updateOrganization(values, successMessage) {
    return core.run(async () => {
      // Renaming returns the new docname, which is also the drill-in key.
      selectedOrganizationName.value = await call('helpdesk.api.organization.update_organization', {
        customer: selectedOrganizationName.value,
        ...values,
      })
    }, successMessage)
  }

  function renameOrganization(value) {
    const name = value.trim()
    if (!name) return toast.error(__('Please enter an organization name'))
    return updateOrganization({ customer_name: name }, __('Organization updated'))
  }

  // A Run Script handler calls functions rather than assigning to a binding.
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
