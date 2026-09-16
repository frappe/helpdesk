import { ref, computed, watch } from 'vue'
import { ROUTES } from '@app/routes'
import { call, toast } from 'frappe-ui'
import { t } from '@app/stores/translations'

// Backed by helpdesk.api.organization.

const MANAGER_ROLE = 'HD Customer Manager'
const MEMBER_ROLE = 'HD Customer'

export function createOrganizationSettings(core) {
  // Null means the list is showing rather than one organization's detail.
  const selectedOrg = ref(null)
  const orgDetail = ref(null)

  const settingsOrg = computed(() => orgDetail.value)
  const isOrgManager = computed(() => Boolean(orgDetail.value?.is_manager))
  const orgMembers = computed(() => orgDetail.value?.members || [])

  // A plain member can read an organization but change nothing in it.
  const managesAnyOrg = computed(() =>
    core.organizations.value.some((org) => org.role !== 'Member'),
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
  const organizationDetailDescription = computed(() =>
    t(
      isOrgManager.value
        ? "Manage your organization's members and tickets."
        : "View your organization's members and tickets.",
    ),
  )

  const canManageMembers = computed(() =>
    Boolean(isOrgManager.value && core.portalConfig.value.allow_customer_managers_to_invite),
  )
  const canEditOrganization = computed(() =>
    Boolean(
      isOrgManager.value &&
        core.portalConfig.value.allow_customer_managers_to_edit_organization,
    ),
  )

  const orgTab = ref('members')
  const orgTabOptions = computed(() => [
    { label: t('Members'), value: 'members' },
    { label: t('Tickets'), value: 'tickets' },
  ])

  const orgName = ref('')
  const inviteOpen = ref(false)
  const inviteEmails = ref([])
  const inviteRole = ref('Member') // 'Member' | 'Manager'
  const inviteContacts = ref([])

  core.afterLoad(() => {
    if (selectedOrg.value) return loadOrganization(selectedOrg.value)
  })

  // --- list -> detail ---

  async function loadOrganization(name) {
    orgTab.value = 'members'
    try {
      orgDetail.value = await call('helpdesk.api.organization.get_organization', {
        customer: name,
      })
      orgName.value = orgDetail.value.customer_name || ''
    } catch (error) {
      console.error(error)
      toast.error(core.serverMessage(error) || 'Could not open organization')
      closeOrganization()
    }
  }

  function openOrganization(name) {
    selectedOrg.value = name
    orgDetail.value = null
    inviteOpen.value = false
    return loadOrganization(name)
  }

  // A list of one is not a choice, however the reader reached the screen.
  watch(
    [core.settingsTab, core.organizations],
    () => {
      if (core.settingsTab.value !== 'members' || selectedOrg.value) return
      if (core.organizations.value.length === 1)
        openOrganization(core.organizations.value[0].name)
    },
    { immediate: true },
  )

  // With one organization there is no list to go back to: the watch above drills straight in.
  const canLeaveOrganization = computed(() => core.organizations.value.length > 1)

  function closeOrganization() {
    selectedOrg.value = null
    orgDetail.value = null
    inviteOpen.value = false
  }

  // --- invites ---

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
    return core.run(async () => {
      const result = await call('frappe.core.api.user_invitation.invite_by_email', {
        emails: emails.join(','),
        roles: [inviteRole.value === 'Manager' ? MANAGER_ROLE : MEMBER_ROLE],
        redirect_to_path: ROUTES.appRoot,
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

  // --- members ---

  // A manager reads every ticket the organization has raised, so the change is spelled out.
  function setMemberRole(member, role) {
    if (member.is_owner || member.pending) return
    const isManager = role === 'Manager'
    if (isManager === Boolean(member.is_manager)) return
    core.askConfirm({
      title: isManager ? 'Grant manager access' : 'Revoke manager access',
      message: isManager
        ? `${member.full_name} will get access to tickets raised by everyone in the organization.`
        : `${member.full_name} will only see their own tickets going forward.`,
      label: 'Confirm',
      // Not destructive either way, so it does not take the dialog's red default.
      theme: 'gray',
      action: () =>
        core.run(
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
    core.askConfirm({
      title: 'Remove member',
      message: `${member.full_name} will lose access to this organization's tickets.`,
      label: 'Remove',
      action: () =>
        core.run(
          () => call('helpdesk.api.organization.remove_member', {
            customer: selectedOrg.value,
            contact: member.contact,
          }),
          'Member removed'
        ),
    })
  }

  function cancelInvitation(member) {
    core.askConfirm({
      title: 'Cancel invitation',
      message: `The invitation sent to ${member.email} will no longer be usable.`,
      label: 'Cancel invitation',
      action: () =>
        core.run(
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

  // --- the organization's own settings ---

  function saveOrganization() {
    const name = orgName.value.trim()
    if (!name) {
      toast.error('Please enter an organization name')
      return
    }
    return core.run(
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

  // A Run Script handler calls functions rather than assigning to a binding.
  function uploadOrgImage() {
    core.pickImage((fileUrl) =>
      core.run(() => call('helpdesk.api.organization.update_organization', {
        customer: selectedOrg.value,
        image: fileUrl,
      }), 'Logo updated')
    )
  }

  function removeOrgImage() {
    return core.run(() => call('helpdesk.api.organization.update_organization', {
      customer: selectedOrg.value,
      image: '',
    }), 'Logo removed')
  }

  return {
    selectedOrg,
    canLeaveOrganization,
    settingsOrg,
    isOrgManager,
    canManageMembers,
    canEditOrganization,
    orgMembers,
    organizationScreenTitle,
    organizationScreenDescription,
    organizationDetailDescription,
    orgTab,
    orgTabOptions,
    orgName,
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
    saveOrganization,
    renameOrganization,
    uploadOrgImage,
    removeOrgImage,
  }
}
