<template>
  <div>
    <Dialog
      v-model="model"
      :options="{ title: 'Add New Customer', size: 'sm' }"
    >
      <template #body-content>
        <div class="space-y-4">
          <div class="space-y-1">
            <Input
              v-model="state.customer"
              label="Customer Name"
              type="text"
              placeholder="Tesla Inc."
            />
          </div>
          <div class="space-y-1">
            <Input
              v-model="state.domain"
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
              @click.prevent="addCustomer"
            />
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive } from "vue";
import { Input, Dialog, createResource } from "frappe-ui";
import { createToast } from "@/utils";

const emit = defineEmits(["customerCreated"]);
const model = defineModel<boolean>();

const state = reactive({
  customer: "",
  domain: "",
});

const customerResource = createResource({
  url: "frappe.client.insert",
  method: "POST",
  data: {
    doc: {
      doctype: "HD Customer",
      customer_name: state.customer,
      domain: state.domain,
    },
  },
  onSuccess: () => {
    state.customer = "";
    state.domain = "";
    createToast({
      title: "Customer Created Successfully ",
      icon: "check",
      iconClasses: "text-green-600",
    });
    emit("customerCreated");
  },
  onError: (err) => {
    createToast({
      title: err.messages[0],
      icon: "x",
      iconClasses: "text-red-600",
    });
  },
});

function addCustomer() {
  if (!state.customer) {
    createToast({
      title: "Customer Name is required",
      icon: "x",
      iconClasses: "text-red-600",
    });
    return;
  }
  customerResource.submit({
    doc: {
      doctype: "HD Customer",
      customer_name: state.customer,
      domain: state.domain,
    },
  });
}
</script>
