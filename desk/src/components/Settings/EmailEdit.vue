<template>
  <div class="flex h-full flex-col gap-4">
    <!-- title and desc -->
    <div role="heading" aria-level="1" class="flex flex-col gap-1">
      <h5 class="text-lg font-semibold">Edit Email</h5>
    </div>
    <div class="w-fit">
      <EmailProviderIcon
        :logo="emailIcon[accountData.service]"
        :service-name="accountData.service"
      />
    </div>
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
    <div class="mt-auto flex justify-between">
      <Button
        label="Back"
        theme="gray"
        variant="outline"
        @click="emit('update:step', 'email-list')"
      />
      <Button
        label="Update Account"
        variant="solid"
        @click="updateAccount"
        :loading="loading"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { call } from "frappe-ui";
import EmailProviderIcon from "./EmailProviderIcon.vue";
import {
  emailIcon,
  services,
  popularProviderFields,
  customProviderFields,
  validateInputs,
} from "./emailConfig";
import { EmailAccountResource } from "@/types";
import { createToast } from "@/utils";

interface Props {
  accountData: EmailAccountResource;
}

const props = withDefaults(defineProps<Props>(), {
  accountData: null,
});

const emit = defineEmits(["update:step"]);

const state = reactive({
  email_account_name: props.accountData.name || "",
  email_id: props.accountData.email_id || "",
  api_key: props.accountData?.api_key || null,
  api_secret: props.accountData?.api_secret || null,
  password: props.accountData?.password || null,
});
const error = ref("");

const isCustomService = computed(() => {
  return services.find((s) => s.name === props.accountData.service).custom;
});

const fields = computed(() => {
  if (isCustomService.value) {
    return customProviderFields;
  }
  return popularProviderFields;
});

const loading = ref(false);
async function updateAccount() {
  error.value = validateInputs(state, isCustomService.value);
  if (error.value) return;
  const old = { ...props.accountData };
  const updatedEmailAccount = { ...state };

  const nameChanged = old.name !== updatedEmailAccount.email_account_name;
  delete old.name;
  delete updatedEmailAccount.email_account_name;

  const otherFieldChanged = isDirty.value;
  const values = updatedEmailAccount;

  if (!nameChanged && !otherFieldChanged) {
    return;
  }

  let name: string;
  if (nameChanged) {
    try {
      name = await callRenameDoc();
      succesHandler();
    } catch (err) {
      errorHandler();
    }
    loading.value = true;
  }
  if (otherFieldChanged) {
    try {
      name = await callSetValue(values);
      succesHandler();
    } catch (err) {
      errorHandler();
    }
  }
  loading.value = false;
}

const isDirty = computed(() => {
  return (
    state.email_id !== props.accountData.email_id ||
    state.api_key !== props.accountData.api_key ||
    state.api_secret !== props.accountData.api_secret ||
    state.password !== props.accountData.password
  );
});

async function callRenameDoc() {
  const d = await call("frappe.client.rename_doc", {
    doctype: "Email Account",
    old_name: props.accountData.name,
    new_name: state.email_account_name,
  });
  return d;
}

async function callSetValue(values) {
  const d = await call("frappe.client.set_value", {
    doctype: "Email Account",
    name: state.email_account_name,
    fieldname: values,
  });
  return d.name;
}

function succesHandler() {
  loading.value = true;
  emit("update:step", "email-list");
  createToast({
    title: "Email account updated successfully",
    icon: "check",
    iconClasses: "text-green-600",
  });
}

function errorHandler() {
  loading.value = false;
  error.value = "Failed to update email account, Invalid credentials";
}
</script>

<style scoped></style>
