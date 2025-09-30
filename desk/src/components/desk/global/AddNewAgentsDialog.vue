<template>
  <Dialog
    :options="{ title: props.title }"
    :model-value="show"
    @update:modelValue="$emit('update:modelValue', $event)"
    @close="close()"
  >
    <template #body-content>
      <div class="space-y-1">
        <div class="border rounded flex flex-1 bg-gray-100">
          <EmailMultiSelect
            class="flex-1"
            :placeholder="__('john@doe.com')"
            inputClass="!bg-white"
            itemClass="bg-white hover:bg-white"
            v-model="invitees"
            :validate="validateEmail"
            :error-message="
              (value) => __('{0} is an invalid email address', [value])
            "
            :emptyPlaceholder="__('Type an email address to invite')"
            :fetchUsers="true"
            variant="subtle"
          />
        </div>
        <div class="text-p-xs text-ink-gray-5">
          {{ __("Type email and press enter to add to the list.") }}
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end items-center">
        <Button
          :disabled="invitees.length == 0"
          appearance="primary"
          @click="sendInvites"
          class="mr-2"
          variant="solid"
          :loading="sentInvitesResource.loading"
        >
          {{ __("Send Invites") }}
        </Button>
        <Button
          :disabled="invitees.length == 0"
          @click="removeAllEmailFromQueue"
        >
          {{ __("Clear All") }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import EmailMultiSelect from "@/components/EmailMultiSelect.vue";
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
import { validateEmail } from "@/utils";
import { createResource, Dialog, FeatherIcon, Input, toast } from "frappe-ui";
import { useOnboarding } from "frappe-ui/frappe";
import { ref } from "vue";

const props = defineProps({
  show: Boolean,
  title: String,
});

const emit = defineEmits(["close", "update:modelValue", "onAgentsInvited"]);

// State
const searchInput = ref("");
const currentInputIsValidEmail = ref(false);
const invitees = ref<string[]>([]);

// Stores and utilities
const { updateOnboardingStep } = useOnboarding("helpdesk");
const { isManager } = useAuthStore();

const removeAllEmailFromQueue = () => {
  invitees.value = [];
};

const close = () => {
  searchInput.value = "";
  invitees.value = [];
  emit("close");
};

// API Resources
const sentInvitesResource = createResource({
  url: "helpdesk.api.agent.sent_invites",
  onSuccess: (res) => {
    emit("onAgentsInvited", invitees.value);
    currentInputIsValidEmail.value = false;
    searchInput.value = "";
    invitees.value = [];

    if (isManager) {
      updateOnboardingStep("invite_agents");
    }

    toast.success("Invites sent successfully!");

    close();
  },
});

const sendInvites = () => {
  sentInvitesResource.submit({
    emails: invitees.value,
  });
};
</script>
