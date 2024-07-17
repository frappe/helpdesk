<template>
  <div>
    <Dialog v-model="open" :options="{ title: 'Create New Contact' }">
      <template #body-content>
        <div class="space-y-4">
          <div class="space-y-1">
            <Input
              v-model="state.emailID"
              label="Email Id"
              type="email"
              @blur="validateEmailInput(state.emailID)"
            />
            <ErrorMessage :message="error.emailValidationError" />
          </div>
          <div class="space-y-1">
            <Input
              v-model="state.firstName"
              label="First Name"
              type="text"
              @blur="validateFirstName(state.firstName)"
            />
            <ErrorMessage :message="error.firstNameValidationError" />
          </div>
          <div class="space-y-1">
            <Input
              v-model="state.lastName"
              label="Last Name (optional)"
              type="text"
            />
            <ErrorMessage :message="error.lastNameValidationError" />
          </div>
          <div class="space-y-1">
            <Input
              v-model="state.phone"
              label="Phone (optional)"
              type="text"
              @blur="validatePhone(state.phone)"
            />
            <ErrorMessage :message="error.phoneValidationError" />
          </div>
          <div class="w-full space-y-1">
            <div>
              <span class="mb-2 block text-sm leading-4 text-gray-700">
                Customer
              </span>
            </div>
            <Autocomplete
              :value="state.selectedCustomer"
              :options="customerResource.data"
              @change="handleCustomerChange"
              @blur="validateCustomer(state.selectedCustomer)"
            />

            <ErrorMessage :message="error.customerValidationError" />
          </div>
          <div class="float-right flex space-x-2">
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

<script setup>
import { ref, computed } from "vue";
import { useContactStore } from "@/stores/contact";

import { Input, Dialog, ErrorMessage } from "frappe-ui";
import { createResource } from "frappe-ui";

import Autocomplete from "@/components/Autocomplete.vue";
import { createToast } from "@/utils";
const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
});

const emit = defineEmits(["update:modelValue", "close", "contactCreated"]);

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

// const formFields = [
//   {
//     label: "Email Id",
//     value: state.value.emailID,
//     error: error.value.emailValidationError,
//     type: "input",
//     action: validateEmailInput(state.value.emailID),
//   },
//   {
//     label: "First Name",
//     value: state.value.firstName,
//     error: error.value.firstNameValidationError,
//     type: "input",
//     action: validateFirstName(state.value.firstName),
//   },
//   {
//     label: "Last Name (optional)",
//     value: state.value.lastName,
//     error: error.value.lastNameValidationError,
//     type: "input",
//   },
//   {
//     label: "Phone (optional)",
//     value: state.value.phone,
//     error: error.value.phoneValidationError,
//     type: "input",
//     action: validatePhone(state.value.phone),
//   },
//   {
//     label: "Customer",
//     value: state.value.selectedCustomer,
//     error: error.value.customerValidationError,
//     action: validateCustomer(state.value.selectedCustomer),
//   },
// ];

const open = computed({
  get: () => props.modelValue,
  set: (val) => {
    emit("update:modelValue", val);
    if (!val) {
      emit("close");
    }
  },
});

const customerResource = createResource({
  url: "helpdesk.extends.client.get_list",
  params: {
    doctype: "HD Customer",
    fields: ["name", "customer_name"],
  },
  transform: (data) => {
    let allData = data.map((option) => {
      return {
        label: option.name,
        value: option.customer_name,
      };
    });
    return allData;
  },
  auto: true,
});

const contactResource = createResource({
  url: "frappe.client.insert",
  onSuccess: (data) => {
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

    emit("contactCreated", data);
  },
  onError: (error) => {
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
  };
  if (state.value.phone) {
    doc.phone_nos = [{ phone: state.value.phone }];
  }

  contactResource.submit({ doc });
}

function handleCustomerChange(item) {
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

function validateEmailInput(value) {
  error.value.emailValidationError = "";
  const reg =
    /^(([^<>()\]\\.,;:\s@"]+(\.[^<>()\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,24}))$/;

  if (!value) {
    error.value.emailValidationError = "Email should not be empty";
  } else if (!reg.test(value)) {
    error.value.emailValidationError = "Enter a valid email";
  } else if (existingContactEmails(contactStore.options).includes(value)) {
    error.value.emailValidationError = "Contact with email already exists";
  }
  return error.value.emailValidationError;
}

function validateFirstName(value) {
  error.value.firstNameValidationError = "";
  if (!value || value.trim() === "") {
    error.value.firstNameValidationError = "First name should not be empty";
  }
  return error.value.firstNameValidationError;
}

function validatePhone(value) {
  error.value.phoneValidationError = "";
  const reg = /[0-9]+/;
  if (value && (!reg.test(value) || value.length < 10)) {
    error.value.phoneValidationError = "Enter a valid phone number";
  }
  return error.value.phoneValidationError;
}

function validateCustomer(value) {
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
