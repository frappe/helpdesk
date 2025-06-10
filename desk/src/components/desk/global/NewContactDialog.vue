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
              <span
                v-if="field.required"
                class="place-self-center text-red-500"
              >
                *
              </span>
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
import { useContactStore } from "@/stores/contact";
import { computed, ref } from "vue";

import {
  Autocomplete,
  Dialog,
  ErrorMessage,
  Input,
  createListResource,
  createResource,
  toast,
} from "frappe-ui";
import zod from "zod";

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
  selectedCustomer: null,
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
  required: boolean;
  action?: () => void;
}

const formFields: FormField[] = [
  {
    label: "Email Id",
    value: "emailID",
    error: "emailValidationError",
    type: "input",
    required: true,
    action: () => validateEmailInput(state.value.emailID),
  },
  {
    label: "First Name",
    value: "firstName",
    error: "firstNameValidationError",
    type: "input",
    required: true,
    action: () => validateFirstName(state.value.firstName),
  },
  {
    label: "Last Name",
    value: "lastName",
    error: "lastNameValidationError",
    type: "input",
    required: false,
  },
  {
    label: "Phone",
    value: "phone",
    error: "phoneValidationError",
    type: "input",
    required: false,
    action: () => validatePhone(state.value.phone),
  },
  {
    label: "Customer",
    value: "selectedCustomer",
    error: "customerValidationError",
    type: "autocomplete",
    required: false,
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
      selectedCustomer: null,
    };
    toast.success("Contact created");
    emit("contactCreated");
  },
});

function createContact() {
  if (validateInputs()) return;

  let doc = {
    doctype: "Contact",
    first_name: state.value.firstName,
    last_name: state.value.lastName,
    email_ids: [{ email_id: state.value.emailID, is_primary: true }],
    links: [],
    phone_nos: [],
  };
  if (state.value.phone) {
    doc.phone_nos = [{ phone: state.value.phone }];
  }
  if (state.value.selectedCustomer) {
    doc.links.push({
      link_doctype: "HD Customer",
      link_name: state.value.selectedCustomer,
    });
  }

  contactResource.submit({ doc });
}

function handleCustomerChange(item: AutoCompleteItem | null) {
  if (!item || item.label === "No label") {
    state.value.selectedCustomer = null;
  } else {
    state.value.selectedCustomer = item.value;
  }
}

function validateInputs() {
  let error = validateEmailInput(state.value.emailID);
  error += validateFirstName(state.value.firstName);
  error += validatePhone(state.value.phone);
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

function existingContactEmails(contacts) {
  return contacts.map((contact) => contact.email_id);
}
</script>

<style></style>
