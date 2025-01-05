<template>
  <div>
    <Dialog v-model="open" :options="{ title: 'Create New Contact' }">
      <template #body-content>
        <div class="space-y-4">
          <div
            v-for="field in formFields"
            :key="field.label"
            class="flex flex-col gap-1"
          >
            <span class="mb-2 block text-sm leading-4 text-gray-700">
              {{ field.label }}
            </span>
            <Input
              v-if="field.type === 'input'"
              v-model="state[field.value]"
              type="text"
              @blur="field.action"
            />
            <Autocomplete
              v-else
              v-model="state[field.value]"
              :options="customerResource.data"
              :value="state[field.value]"
              @update:model-value="handleCustomerChange"
            />
            <ErrorMessage :message="error[field.error]" />
          </div>
          <div class="flex justify-end space-x-2">
            <Button
              label="Create"
              :loading="contactResource.loading"
              theme="gray"
              variant="solid"
              @click="createContact()"
            />
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useContactStore } from "@/stores/contact";

import {
  Input,
  Dialog,
  ErrorMessage,
  createResource,
  Autocomplete,
  createListResource,
} from "frappe-ui";
import zod from "zod";

import { createToast } from "@/utils";
import { AutoCompleteItem } from "@/types";

interface Props {
  modelValue: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (event: "update:modelValue", value: boolean): void;
  (event: "close"): void;
  (event: "contactCreated"): void;
}>();

const contactStore = useContactStore();

const state = ref({
  emailID: "",
  firstName: "",
  lastName: "",
  phone: "",
  selectedCustomer: "",
});

const error = ref({
  emailValidationError: "",
  firstNameValidationError: "",
  lastNameValidationError: "",
  phoneValidationError: "",
  customerValidationError: "",
});

interface FormField {
  label: string;
  value: string;
  error: string;
  type: string;
  action?: () => void;
}

const formFields: FormField[] = [
  {
    label: "Email Id",
    value: "emailID",
    error: "emailValidationError",
    type: "input",
    action: () => validateEmailInput(state.value.emailID),
  },
  {
    label: "First Name",
    value: "firstName",
    error: "firstNameValidationError",
    type: "input",
    action: () => validateFirstName(state.value.firstName),
  },
  {
    label: "Last Name",
    value: "lastName",
    error: "lastNameValidationError",
    type: "input",
  },
  {
    label: "Phone",
    value: "phone",
    error: "phoneValidationError",
    type: "input",
    action: () => validatePhone(state.value.phone),
  },
  {
    label: "Customer",
    value: "selectedCustomer",
    error: "customerValidationError",
    type: "autocomplete",
    action: () => validateCustomer(state.value.selectedCustomer),
  },
];

const open = computed({
  get: () => props.modelValue,
  set: (val) => {
    emit("update:modelValue", val);
    if (!val) {
      emit("close");
    }
  },
});

const customerResource = createListResource({
  doctype: "HD Customer",
  fields: ["name"],
  cache: "customers",
  transform: (data) => {
    return data.map((option) => {
      return {
        label: option.name,
        value: option.name,
      };
    });
  },
  auto: true,
});

const contactResource = createResource({
  url: "frappe.client.insert",
  onSuccess: () => {
    state.value = {
      emailID: "",
      firstName: "",
      lastName: "",
      phone: "",
      selectedCustomer: "",
    };
    createToast({
      title: "Contact Created Successfully ",
      icon: "check",
      iconClasses: "text-green-600",
    });
    emit("contactCreated");
  },
  onError: (error: Error) => {
    createToast({
      title: "Contact Creation Failed",
      message: error.message,
      icon: "error",
      iconClasses: "text-red-600",
    });
  },
});

function createContact() {
  if (validateInputs()) return;

  let doc = {
    doctype: "Contact",
    first_name: state.value.firstName,
    last_name: state.value.lastName,
    email_ids: [{ email_id: state.value.emailID, is_primary: true }],
    links: [
      {
        link_doctype: "HD Customer",
        link_name: state.value.selectedCustomer,
      },
    ],
    phone_nos: [],
  };
  if (state.value.phone) {
    doc.phone_nos = [{ phone: state.value.phone }];
  }

  contactResource.submit({ doc });
}

function handleCustomerChange(item: AutoCompleteItem) {
  if (!item) return;
  state.value.selectedCustomer = item.value;
}

function validateInputs() {
  let error = validateEmailInput(state.value.emailID);
  error += validateFirstName(state.value.firstName);
  error += validatePhone(state.value.phone);
  error += validateCustomer(state.value.selectedCustomer);
  return error;
}

function validateEmailInput(value: string) {
  error.value.emailValidationError = "";
  const success = zod.string().email().safeParse(value).success;

  if (!value) {
    error.value.emailValidationError = "Email should not be empty";
  } else if (!success) {
    error.value.emailValidationError = "Enter a valid email";
  } else if (existingContactEmails(contactStore.options).includes(value)) {
    error.value.emailValidationError = "Contact with email already exists";
  }
  return error.value.emailValidationError;
}

function validateFirstName(value: string) {
  error.value.firstNameValidationError = "";
  if (!value || value.trim() === "") {
    error.value.firstNameValidationError = "First name should not be empty";
  }
  return error.value.firstNameValidationError;
}

function validatePhone(value: string) {
  error.value.phoneValidationError = "";
  const reg = /[0-9]+/;
  if (value && (!reg.test(value) || value.length < 10)) {
    error.value.phoneValidationError = "Enter a valid phone number";
  }
  return error.value.phoneValidationError;
}

function validateCustomer(value: string) {
  error.value.customerValidationError = "";
  if (!value || value.trim() === "") {
    error.value.customerValidationError = "Customer should not be empty";
  }
  return error.value.customerValidationError;
}

function existingContactEmails(contacts) {
  return contacts.map((contact) => contact.email_id);
}
</script>

<style></style>
