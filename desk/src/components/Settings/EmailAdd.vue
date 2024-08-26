<template>
  <div class="flex h-full flex-col gap-4">
    <!-- title and desc -->
    <div role="heading" aria-level="1" class="flex flex-col gap-1">
      <h5 class="text-lg font-semibold">Setup Email</h5>
      <p class="text-sm text-gray-600">
        Choose the email service provider you want to configure.
      </p>
    </div>
    <!-- email service provider selection -->
    <div class="flex flex-wrap items-center gap-4">
      <div
        v-for="s in services"
        :key="s.name"
        class="min-w-3 mt-4 flex flex-col items-center gap-1"
        @click="handleSelect(s)"
      >
        <EmailProviderIcon
          :service-name="s.name"
          :logo="s.icon"
          :selected="selectedService?.name === s?.name"
        />
      </div>
    </div>
    <div v-if="selectedService" class="flex flex-col gap-4">
      <!-- email service provider info -->
      <div class="flex items-center gap-2 rounded-md p-2 ring-1 ring-gray-200">
        <IconAlert class="h-8 min-w-[5%] text-blue-500" />
        <div class="text-wrap text-xs text-gray-700">
          {{ selectedService.info }}
          <a
            :href="selectedService.link"
            target="_blank"
            class="text-blue-500 underline"
            >here</a
          >
          .
        </div>
      </div>
      <!-- service provider fields -->
      <div class="flex flex-col gap-2">
        <div class="grid grid-cols-1 gap-4">
          <div
            v-for="field in fields"
            :key="field.name"
            class="flex flex-col gap-1"
          >
            <FormControl
              v-model="state[field.name]"
              :label="field.label"
              :name="field.name"
              :type="field.type"
              :placeholder="field.placeholder"
            />
          </div>
        </div>
        <ErrorMessage v-if="error" class="ml-1" :message="error" />
      </div>
    </div>
    <div v-if="selectedService" class="mt-auto flex justify-between">
      <Button
        label="Back"
        theme="gray"
        variant="outline"
        :disabled="addEmailRes.loading"
        @click="emit('update:step', 'email-list')"
      />
      <Button
        label="Create"
        variant="solid"
        :loading="addEmailRes.loading"
        @click="createEmailAccount"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, Reactive, reactive, Ref, ref } from "vue";
import { createResource } from "frappe-ui";
import IconAlert from "~icons/espresso/alert-circle";
import { createToast } from "@/utils";
import {
  customProviderFields,
  popularProviderFields,
  services,
  validateInputs,
} from "./emailConfig";
import EmailProviderIcon from "./EmailProviderIcon.vue";
import { EmailService, EmailState, EmailStep } from "@/types";

interface E {
  (event: "update:step", value: EmailStep): void;
}

const emit = defineEmits<E>();

const state: Reactive<EmailState> = reactive({
  service: "",
  email_account_name: "",
  email_id: "",
  password: "",
  api_key: "",
  api_secret: "",
});

function resetState() {
  state.email_account_name = "";
  state.email_id = "";
  state.password = "";
  state.api_key = "";
}

const selectedService: Ref<EmailService> = ref(null);
const fields = computed(() =>
  selectedService.value.custom ? customProviderFields : popularProviderFields
);

function handleSelect(service: EmailService) {
  selectedService.value = service;
  state.service = service.name;
}

const addEmailRes = createResource({
  url: "helpdesk.api.settings.create_email_account",
  makeParams: (val: EmailState) => {
    return {
      ...val,
    };
  },
  onSuccess: () => {
    resetState();
    createToast({
      title: "Email account created successfully",
      icon: "check",
      iconClasses: "text-green-600",
    });
    emit("update:step", "email-list");
  },
  onError: () => {
    error.value = "Failed to create email account, Invalid credentials";
  },
});

const error = ref("");
function createEmailAccount() {
  error.value = validateInputs(state, selectedService.value.custom);
  if (error.value) return;
  addEmailRes.submit({ ...state });
}
</script>

<style scoped></style>
