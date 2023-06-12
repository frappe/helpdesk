<template>
  <div>
    <Dialog v-model="open" :options="{ title: 'Add New Customer', size: 'sm' }">
      <template #body-content>
        <div class="space-y-4">
          <div class="space-y-1">
            <Input
              v-model="customer"
              label="Customer Name"
              type="text"
              placeholder="Tesla Inc."
            />
          </div>
          <div class="space-y-1">
            <Input
              v-model="domain"
              label="Domain"
              type="text"
              placeholder="eg: tesla.com, mycompany.com"
            />
          </div>
          <div class="float-right flex space-x-2">
            <Button
              label="Add"
              theme="gray"
              variant="solid"
              @click="
                () => {
                  addCustomer();
                  close();
                  $router.go();
                }
              "
            />
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script>
import { Input, Dialog, ErrorMessage } from "frappe-ui";
import { computed, ref, inject } from "vue";
export default {
  name: "NewCustomerDialog",
  components: {
    Dialog,
    Input,
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
  },
  setup(props, { emit }) {
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
    };
  },
  data() {
    return {
      customer: "",
      domain: "",
    };
  },
  methods: {
    addCustomer() {
      const inputParams = {
        customer_name: this.customer,
        domain: this.domain,
      };
      this.$resources.newCustomer.submit({
        doc: {
          doctype: "HD Customer",
          ...inputParams,
        },
      });
    },
    close() {
      this.customer = "";
      this.domain = "";
      this.$emit("close");
    },
  },
  resources: {
    newCustomer() {
      return {
        url: "frappe.client.insert",
        onSuccess: (doc) => {
          this.$router.push(`/customers`);
        },
      };
    },
  },
};
</script>
