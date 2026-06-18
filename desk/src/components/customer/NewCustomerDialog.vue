<template>
  <Dialog v-model:open="model" :title="__('Create customer')" size="lg">
    <template #default>
      <div class="space-y-4">
        <ImageAvatar
          v-model="state.image"
          :label="__('Logo')"
          :description="__('Upload a PNG or JPG, 128x128 recommended')"
          :fallback-label="state.name || 'Customer'"
          shape="square"
        />

        <FormControl
          class="[&_p]:text-p-xs"
          type="text"
          :label="__('Name')"
          :required="true"
          placeholder="Frappe"
          v-model="state.name"
        />

        <div class="grid grid-cols-2 gap-4">
          <FormControl
            class="[&_p]:text-p-xs [&_[data-slot=trigger]]:w-full"
            type="select"
            :label="__('Customer Type')"
            :options="customerTypeOptions"
            v-model="state.customerType"
          />
          <Link
            :label="__('Country')"
            placeholder="India"
            doctype="Country"
            v-model="state.country"
          >
            <template #prefix>
              <LucideMapPin class="size-4 mr-1.5" />
            </template>
          </Link>
        </div>

        <FormControl
          class="[&_p]:text-p-xs"
          type="text"
          :label="__('Domain')"
          placeholder="frappe.io"
          v-model="state.domain"
        >
          <template #prefix>
            <LucideGlobe class="size-4" />
          </template>
        </FormControl>

        <hr class="border-outline-gray-2" />

        <div class="space-y-4">
          <h3 class="text-base font-medium text-ink-gray-8">
            {{ __("Primary Contact") }}
            <span class="text-p-sm font-normal text-ink-gray-5">
              {{ __("(optional)") }}
            </span>
          </h3>
          <div class="grid grid-cols-2 gap-4">
            <FormControl
              class="[&_p]:text-p-xs"
              type="text"
              :label="__('First Name')"
              placeholder="John"
              v-model="primaryContact.firstName"
            />
            <FormControl
              class="[&_p]:text-p-xs"
              type="text"
              :label="__('Last Name')"
              placeholder="Doe"
              v-model="primaryContact.lastName"
            />
          </div>
          <FormControl
            class="[&_p]:text-p-xs"
            type="email"
            :label="__('Email')"
            placeholder="name@company.com"
            v-model="primaryContact.email"
          />
          <PhoneControl
            :label="__('Mobile Number')"
            v-model="primaryContact.mobileNo"
          />
        </div>
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          :label="__('Cancel')"
          @click="
            () => {
              reset();
              model = false;
            }
          "
        />
        <Button
          :label="__('Create')"
          theme="gray"
          variant="solid"
          :loading="customerResource.loading"
          @click.prevent="addCustomer"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import ImageAvatar from "@/components/ImageAvatar.vue";
import {
  customerTypeOptions,
  useNewCustomerForm,
} from "@/composables/customer";
import { __ } from "@/translation";
import type { Resource } from "@/types";
import { getErrorMessage, validateEmailWithZod } from "@/utils";
import { Button, Dialog, FormControl, createResource, toast } from "frappe-ui";
import { useRouter } from "vue-router";
import LucideGlobe from "~icons/lucide/globe";
import LucideMapPin from "~icons/lucide/map-pin";
import Link from "../frappe-ui/Link.vue";
import PhoneControl from "../frappe-ui/PhoneControl/PhoneControl.vue";

const model = defineModel<boolean>({ default: false });
const router = useRouter();

const { state, primaryContact, reset } = useNewCustomerForm();

const customerResource: Resource = createResource({
  url: "helpdesk.api.customer.create_customer",
  method: "POST",
  onSuccess: (name: string) => {
    router.push({ name: "Customer", params: { id: name } });
    toast.success(__("Customer created"));
  },
  onError: (error: unknown) => {
    getErrorMessage(error, true);
  },
});

function addCustomer() {
  if (!state.name) {
    toast.error(__("Name is required"));
    return;
  }
  if (primaryContact.email && !validateEmailWithZod(primaryContact.email)) {
    toast.error(__("Invalid email address"));
    return;
  }
  customerResource.submit({
    customer: {
      customer_name: state.name,
      customer_type: state.customerType,
      domain: state.domain,
      image: state.image,
      country: state.country,
    },
    primary_contact: primaryContact.email
      ? {
          first_name: primaryContact.firstName,
          last_name: primaryContact.lastName,
          email: primaryContact.email,
          mobile_no: primaryContact.mobileNo,
        }
      : null,
  });
}
</script>
