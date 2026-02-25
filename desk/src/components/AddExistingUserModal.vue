<template>
  <Dialog
    v-model="show"
    :options="{
      title: forAgents ? __('Add Existing User') : __('Add Existing Contact'),
    }"
    @close="
      () => {
        show = false;
        newUsers = [];
      }
    "
  >
    <template #body-content>
      <div class="flex gap-1 border rounded mb-4 p-2 text-ink-gray-5">
        <FeatherIcon name="info" class="size-3.5 mt-0.5 shrink-0" />
        <p class="text-p-sm">{{ infoText }}</p>
      </div>

      <!-- EmailMultiSelect will go here -->
      <div class="p-2 group bg-surface-gray-2 hover:bg-surface-gray-3 rounded">
        <EmailMultiSelect
          ref="emailMultiSelect"
          class="flex-1"
          inputClass="!bg-surface-gray-2 hover:!bg-surface-gray-3 group-hover:!bg-surface-gray-3"
          :placeholder="
            forAgents ? __('Search users...') : __('Search contacts...')
          "
          :existingUsers="props.existingUsers"
          :forAgents="forAgents"
          :validate="forAgents ? validateEmailWithZod : null"
          v-model="newUsers"
          :emptyPlaceholder="
            forAgents ? __('No Users Found') : __('No Contacts Found')
          "
        />
      </div>

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
          :label="__('Add')"
          :disabled="!newUsers.length"
          @click="handleInviteUser()"
          :loading="loading"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
import { __ } from "@/translation";
import { validateEmailWithZod } from "@/utils";
import { Button, Dialog, FeatherIcon, FormControl } from "frappe-ui";
import { computed, ref, watch } from "vue";
import EmailMultiSelect from "./EmailMultiSelect.vue";

const props = defineProps<{
  forAgents?: boolean;
  existingUsers?: string[];
  loading?: boolean;
}>();
// define emits with type
const emit = defineEmits<{
  (e: "invited", data: { users: string[]; role: string }): void;
}>();

const show = defineModel<boolean>({ default: false });

const { users } = useUserStore();
const { isManager } = useAuthStore();

const emailMultiSelect = ref<{ setFocus: () => void } | null>(null);
const newUsers = ref<string[]>([]);
const role = ref(props.forAgents ? "Agent" : "HD Customer");

watch(show, (val) => {
  if (val) setTimeout(() => emailMultiSelect.value?.setFocus(), 100);
});

const infoText = computed<string>(() => {
  return props.forAgents
    ? __(
        "Add existing system users to Helpdesk. Assign them a role to grant access with their current credentials."
      )
    : __(
        "Add existing system users as contacts for this customer. Assign them a role to define their level of access."
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
  // emit invited with users
  emit("invited", { users: newUsers.value, role: role.value });
  newUsers.value = [];
  show.value = false;
}
</script>
