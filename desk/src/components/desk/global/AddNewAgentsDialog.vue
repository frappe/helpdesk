<template>
  <Dialog
    :options="{ title: 'Add Agents' }"
    :model-value="show"
    @update:modelValue="$emit('update:modelValue', $event)"
    @close="close()"
  >
    <template #body-content>
      <div class="space-y-3">
        <form
          @submit.prevent="onSubmit"
          class="flex flex-row items-center space-x-2"
        >
          <Input
            id="searchInput"
            class="w-full"
            type="text"
            v-model="searchInput"
            placeholder="Type emails"
            @input="(val) => onSearchInputChange(val)"
          />
          <Button
            appearance="primary"
            type="submit"
            :disabled="!currentInputIsValidEmail"
            @click="
              () => {
                addToInviteQueue(searchInput);
                clearSearchInput();
              }
            "
          >
            Add
          </Button>
        </form>
        <div
          class="flex max-h-[300px] min-h-[100px] flex-col overflow-y-auto rounded border bg-gray-100 px-2"
          v-if="inviteQueue.length"
        >
          <ul class="flex flex-wrap gap-2 py-2">
            <li
              class="flex items-center space-x-2 rounded bg-white p-1 shadow"
              v-for="email in inviteQueue.slice().reverse()"
              :key="email"
              :title="email"
            >
              <span class="ml-2 text-base">
                {{ email }}
              </span>
              <button
                class="grid h-4 w-4 place-items-center rounded text-gray-700 hover:bg-gray-300"
                @click="removeEmailFromQueue(email)"
              >
                <FeatherIcon class="w-3" name="x" />
              </button>
            </li>
          </ul>
        </div>
      </div>
    </template>
    <template #actions v-if="inviteQueue.length">
      <div class="flex justify-end items-center">
        <Button
          :disabled="inviteQueue.length == 0"
          appearance="primary"
          @click="sendInvites"
          class="mr-2"
          variant="solid"
          :loading="sentInvitesResource.loading"
          >Send Invites
        </Button>
        <Button @click="removeAllEmailFromQueue"> Clear All </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { useAuthStore } from "@/stores/auth";
import { createResource, Dialog, FeatherIcon, Input, toast } from "frappe-ui";
import { useOnboarding } from "frappe-ui/frappe";
import { ref } from "vue";

const props = defineProps({
  show: Boolean,
});

const emit = defineEmits(["close", "update:modelValue"]);

// State
const searchInput = ref("");
const inviteQueue = ref([]);
const currentInputIsValidEmail = ref(false);

// Stores and utilities
const { updateOnboardingStep } = useOnboarding("helpdesk");
const { isManager } = useAuthStore();

// Methods
const testEmailRegex = (val) => {
  let emailRegex = /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/;
  return emailRegex.test(val);
};

const onSearchInputChange = (val) => {
  val = val.replaceAll(" ", "");
  if (val == "") {
    document.getElementById("searchInput").value = "";
    return;
  }

  const valStr = val;
  const inputs = val.split(",");

  let clearInputFlag = false;
  currentInputIsValidEmail.value = false;

  inputs.forEach((input) => {
    if (testEmailRegex(input)) {
      if (inputs.length > 1) {
        addToInviteQueue(input);
        clearInputFlag = true;
      } else {
        if (valStr.includes(",")) {
          addToInviteQueue(input);
          clearInputFlag = true;
        } else {
          currentInputIsValidEmail.value = true;
        }
      }
    }
  });

  if (clearInputFlag) {
    clearSearchInput();
  }
};

const addToInviteQueue = (email) => {
  inviteQueue.value = [...new Set([...inviteQueue.value, email])];
};

const removeEmailFromQueue = (email) => {
  inviteQueue.value = inviteQueue.value.filter((item) => item !== email);
};

const removeAllEmailFromQueue = () => {
  inviteQueue.value = [];
};

const clearSearchInput = () => {
  currentInputIsValidEmail.value = false;
  searchInput.value = "";

  const input = document.getElementById("searchInput");
  input.value = "";
  input.focus();
};

const close = () => {
  searchInput.value = "";
  inviteQueue.value = [];
  emit("close");
};

// API Resources
const sentInvitesResource = createResource({
  url: "helpdesk.api.agent.sent_invites",
  onSuccess: (res) => {
    currentInputIsValidEmail.value = false;
    searchInput.value = "";
    inviteQueue.value = [];

    if (isManager) {
      updateOnboardingStep("invite_agents");
    }

    toast.success("Invites sent successfully!");

    close();
  },
});

const sendInvites = () => {
  sentInvitesResource.submit({
    emails: inviteQueue.value,
  });
};
</script>
