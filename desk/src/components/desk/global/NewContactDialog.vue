<template>
  <div>
    <Dialog v-model="open" :options="{ title: 'Create New Contact' }">
      <template #body-content>
        <div class="space-y-4">
          <div class="space-y-1">
            <Input v-model="emailId" label="Email Id" type="email" />
            <ErrorMessage :message="emailValidationError" />
          </div>
          <div class="space-y-1">
            <Input v-model="firstName" label="First Name" type="text" />
            <ErrorMessage :message="firstNameValidationError" />
          </div>
          <div class="space-y-1">
            <Input
              v-model="lastName"
              label="Last Name (optional)"
              type="text"
            />
            <ErrorMessage :message="lastNameValidationError" />
          </div>
          <div class="space-y-1">
            <Input v-model="phone" label="Phone (optional)" type="text" />
            <ErrorMessage :message="phoneValidationError" />
          </div>
          <div class="w-full space-y-1">
            <div>
              <span class="mb-2 block text-sm leading-4 text-gray-700">
                Customer
              </span>
            </div>
            <Autocomplete
              :value="fdCustomer != null ? fdCustomer : selectedCustomer"
              :resource-options="{
                url: 'helpdesk.extends.client.get_list',
                inputMap: (query) => {
                  return {
                    doctype: 'HD Customer',
                    pluck: 'name',
                    filters: [['name', 'like', `%${query}%`]],
                  };
                },
                responseMap: (res) => {
                  return res.map((d) => {
                    return {
                      label: d.name,
                      value: d.name,
                    };
                  });
                },
              }"
              @change="
                (item) => {
                  if (!item) {
                    return;
                  }
                  selectedCustomer = item.value;
                }
              "
            />
            <ErrorMessage :message="customerValidationError" />
          </div>
          <div class="float-right flex space-x-2">
            <Button
              label="Create"
              :loading="$resources.createContact.loading"
              theme="gray"
              variant="solid"
              @click="validateInputs() ? null : createContact()"
            />
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script>
import { Input, Dialog, ErrorMessage } from "frappe-ui";
import { computed, ref } from "vue";
import Autocomplete from "@/components/global/Autocomplete.vue";
import { useContactStore } from "@/stores/contact";
export default {
  name: "NewContactDialog",
  components: {
    Input,
    Dialog,
    ErrorMessage,
    Autocomplete,
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
    fdCustomer: {
      type: String,
      default: null,
    },
  },
  setup(props, { emit }) {
    const contactStore = useContactStore();
    const emailValidationError = ref("");
    const firstNameValidationError = ref("");
    const lastNameValidationError = ref("");
    const phoneValidationError = ref("");
    const customerValidationError = ref("");
    const selectedCustomer = ref("");
    let open = computed({
      get: () => props.modelValue,
      set: (val) => {
        emit("update:modelValue", val);
        if (!val) {
          emit("close");
        }
      },
    });

    return {
      open,
      contactStore,
      emailValidationError,
      firstNameValidationError,
      lastNameValidationError,
      phoneValidationError,
      customerValidationError,
      selectedCustomer,
    };
  },
  data(props) {
    return {
      firstName: "",
      lastName: "",
      emailId: "",
      phone: "",
      customer: "",
    };
  },
  watch: {
    emailId(newValue) {
      this.validateEmailInput(newValue);
    },
    firstName(newValue) {
      this.validateFirstName(newValue);
    },
    phone(newValue) {
      this.validatePhone(newValue);
    },
    customer(newValue) {
      this.validateCustomer(newValue);
    },
  },
  resources: {
    createContact() {
      return {
        url: "frappe.client.insert",
        onSuccess: (data) => {
          this.emailId = "";
          this.firstName = "";
          this.lastName = "";
          this.phone = "";
          this.customer = "";
          this.$emit("contactCreated", data);
        },
      };
    },
    getCustomers() {
      return {
        url: "helpdesk.extends.client.get_list",
        params: {
          doctype: "HD Customer",
          fields: ["name", "customer_name"],
        },
        auto: true,
      };
    },
  },
  methods: {
    createContact() {
      if (this.validateInputs()) {
        return;
      }
      let doc = {
        doctype: "Contact",
        first_name: this.firstName,
        last_name: this.lastName,
        email_ids: [{ email_id: this.emailId, is_primary: true }],
        links: [
          {
            link_doctype: "HD Customer",
            link_name:
              this.fdCustomer != null ? this.fdCustomer : this.selectedCustomer,
          },
        ],
      };
      if (this.phone) {
        doc.phone_nos = [{ phone: this.phone }];
      }
      this.$resources.createContact.submit({
        doc,
      });
    },
    validateInputs() {
      let error = this.validateEmailInput(this.emailId);
      error += this.validateFirstName(this.firstName);
      error += this.validatePhone(this.phone);
      error += this.validateCustomer(
        this.fdCustomer != null ? this.fdCustomer : this.selectedCustomer
      );
      return error;
    },
    validateEmailInput(value) {
      function existingContactEmails(contacts) {
        let list = [];
        for (let index in contacts) {
          list.push(contacts[index].email_id);
        }
        return list;
      }
      this.emailValidationError = "";
      const reg =
        /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,24}))$/;
      if (!value) {
        this.emailValidationError = "Email should not be empty";
      } else if (!reg.test(value)) {
        this.emailValidationError = "Enter a valid email";
      } else if (
        existingContactEmails(this.contactStore.options).includes(value)
      ) {
        this.emailValidationError = "Contact with email already exists";
      }
      return this.emailValidationError;
    },
    validateFirstName(value) {
      this.firstNameValidationError = "";
      if (!value) {
        this.firstNameValidationError = "First name should not be empty";
      } else if (value.trim() == "") {
        this.firstNameValidationError = "First name should not be empty";
      }
      return this.firstNameValidationError;
    },
    validatePhone(value) {
      this.phoneValidationError = "";
      const reg = /[0-9]+/;
      if (!value) {
        this.phoneValidationError = "";
      } else if (!reg.test(value) || value.length < 10) {
        this.phoneValidationError = "Enter a valid phone number";
      }
      return this.phoneValidationError;
    },
    validateCustomer(value) {
      this.customerValidationError = "";
      if (!value) {
        this.customerValidationError = "Customer should not be empty";
      } else if (value.trim() == "") {
        this.customerValidationError = "Customer should not be empty";
      }
      return this.customerValidationError;
    },
  },
};
</script>

<style></style>
