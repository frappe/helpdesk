<template>
  <div>
    <Dialog
      v-model="model"
      :options="{ title: __('Add New Customer'), size: 'sm' }"
    >
      <template #body-content>
        <div class="space-y-4">
          <div class="space-y-1">
            <Input
              v-model="state.customer"
              :label="__('Customer Name')"
              type="text"
              :placeholder="__('Tesla Inc.')"
            />
          </div>
          <div class="space-y-1">
            <Input
              v-model="state.domain"
              :label="__('Domain')"
              type="text"
              :placeholder="__('eg: tesla.com, mycompany.com')"
            />
          </div>
          <div class="float-right flex space-x-2">
            <Button
              :label="__('Add')"
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
import { Dialog, Input, createResource, toast } from "frappe-ui";
import { reactive } from "vue";
import { __ } from "@/translation";

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
    toast.success(__("Customer created"));
    emit("customerCreated");
  },
  onError: (err) => {
    toast.error(err.messages[0]);
  },
});

function addCustomer() {
  if (!state.customer) {
    toast.error(__("Customer name is required"));
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
