<template>
  <Dialog
    v-model="show"
    :options="{
      title: forAgents
        ? __('Add Existing User')
        : inviteNew
        ? __('Invite New Contact')
        : __('Add Existing Contact'),
    }"
    @close="handleDialogClose()"
  >
    <template #body-content>
      <div class="flex gap-1 border rounded mb-4 p-2 text-ink-gray-5">
        <LucideInfo class="size-3.5 mt-[4px] shrink-0" />
        <p class="text-p-sm">{{ infoText }}</p>
      </div>

      <div
        class="p-2 group bg-surface-gray-2 hover:bg-surface-gray-3 rounded"
        v-if="!inviteNew"
      >
        <EmailMultiSelect
          ref="emailMultiSelect"
          class="flex-1"
          inputClass="!bg-surface-gray-2 hover:!bg-surface-gray-3 group-hover:!bg-surface-gray-3"
          :placeholder="
            forAgents ? __('Search users...') : __('Search contacts...')
          "
          :existingUsers="existingUsers"
          :forAgents="forAgents"
          :validate="forAgents ? validateEmailWithZod : null"
          v-model="selectedContacts"
          :emptyPlaceholder="
            forAgents ? __('No Users Found') : __('No Contacts Found')
          "
        />
      </div>
      <TagInput
        v-else
        ref="tagInput"
        :placeholder="__('Enter emails, comma separated ')"
        :validate="validateEmailWithZod"
        v-model="newUsers"
        :label="__('Invite by email')"
        :description="
          __(
            'Type an email and press Enter or comma to add it. You can also paste a comma-separated list.'
          )
        "
        :error-message="(input:string)=> `${input} ${__('is not a valid email address.')}` "
      />

      <FormControl
        type="select"
        class="mt-4"
        v-model="role"
        :label="__('Role')"
        :options="roleOptions"
        :description="roleDescription"
      />
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="solid"
          :label="inviteNew ? __('Invite') : __('Add')"
          @click="handleInviteUser()"
          :loading="loading"
          :disabled="
            inviteNew
              ? !newUsers.length || tagInput?.hasError
              : !selectedContacts.length
          "
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
import { validateEmailWithZod } from "@/utils";
import { Button, Dialog, FormControl, toast } from "frappe-ui";
import { computed, ref, watch } from "vue";
import EmailMultiSelect from "./EmailMultiSelect.vue";
import TagInput from "./TagInput.vue";

const props = withDefaults(
  defineProps<{
    forAgents?: boolean;
    existingUsers?: string[];
    loading?: boolean;
    inviteNew?: boolean;
  }>(),
  {
    forAgents: false,
    existingUsers: () => [],
    loading: false,
    inviteNew: false,
  }
);
// define emits with type
const emit = defineEmits<{
  (e: "addedExisting", data: { contacts: string[]; role: string }): void;
  (e: "invited", data: { users: string; role: string }): void;
}>();

const show = defineModel<boolean>({ default: false });

const { isManager } = useAuthStore();

const emailMultiSelect = ref<{ setFocus: () => void } | null>(null);
const tagInput = ref<{ setFocus: () => void; hasError: boolean } | null>(null);
const selectedContacts = ref<string[]>([]);
const newUsers = ref<string[]>([]);
const role = ref(props.forAgents ? "Agent" : "HD Customer");

watch(show, (val) => {
  if (val)
    setTimeout(() => {
      if (props.inviteNew) tagInput.value?.setFocus();
      else emailMultiSelect.value?.setFocus();
    }, 100);
});

const infoText = computed<string>(() => {
  return props.forAgents
    ? __(
        "Add existing system users to Helpdesk. Assign them a role to grant access with their current credentials."
      )
    : props.inviteNew
    ? __(
        "Invite new contacts to Helpdesk by adding their email addresses. Assign them a role to define their level of access."
      )
    : __(
        "Add existing contacts as system users for this customer. Assign them a role to define their level of access."
      );
});

const roleOptions = computed(() => {
  if (props.forAgents) {
    return [
      { value: "Agent", label: __("Agent") },
      ...(isManager()
        ? [{ value: "Agent Manager", label: __("Manager") }]
        : []),
    ];
  }
  return [
    { value: "HD Customer", label: __("Customer") },
    { value: "HD Customer Manager", label: __("Customer Manager") },
  ];
});

const roleDescription = computed<string>(() => {
  const descriptions: Record<string, string> = {
    "HD Customer Manager": __(
      "Has access to all tickets raised by the organisation. Can designate other members as managers and raise tickets on behalf of the organisation."
    ),
    "HD Customer": __(
      "Can raise tickets on behalf of the organisation and view only the tickets raised by them."
    ),
    "Agent Manager": __(
      "Can manage and invite new users, and create public & private views (reports)."
    ),
    Agent: __("Can work with tickets and create private views (reports)."),
  };
  return descriptions[role.value] ?? "";
});

function handleInviteUser() {
  // emit invited with contacts
  if (props.inviteNew) {
    inviteNewUsers();
  } else {
    addExistingContacts();
  }
  selectedContacts.value = [];
}
function inviteNewUsers() {
  if (!newUsers.value.length) {
    toast.error(__("At least one email required"));
    return;
  }
  emit("invited", { users: newUsers.value.join(","), role: role.value });
  newUsers.value = [];
}

function addExistingContacts() {
  emit("addedExisting", { contacts: selectedContacts.value, role: role.value });
}

function handleDialogClose() {
  show.value = false;
  if (props.inviteNew) {
    newUsers.value = [];
  } else {
    selectedContacts.value = [];
  }
}
</script>
