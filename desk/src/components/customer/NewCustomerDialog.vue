<template>
  <div>
    <Dialog
      v-model="model"
      :options="{ title: __('New Customer'), size: 'lg' }"
      @after-leave="reset"
    >
      <template #body-content>
        <div class="space-y-4">
          <div class="flex gap-4 items-center">
            <Avatar
              v-if="state.image"
              :image="state.image"
              :label="state.name || 'Customer'"
              shape="circle"
              size="3xl"
            />
            <div
              class="flex size-11.5 items-center justify-center bg-surface-gray-2 uppercase text-ink-gray-5 select-none font-medium text-2xl rounded-full"
              v-else
            >
              <OrganizationsIcon class="size-8" />
            </div>
            <FileUploader
              :fileTypes="['image/*']"
              @success="(file: File) => (state.image = file.file_url)"
            >
              <template
                #default="{ openFileSelector, error: _error, uploading }"
              >
                <div class="space-x-2">
                  <Button
                    variant="subtle"
                    @click.prevent="openFileSelector()"
                    tooltip="Upload Image"
                    label="Upload Image"
                  />
                  <!-- remove button if state.image exists -->
                  <Button
                    v-if="state.image"
                    label="Remove"
                    variant="subtle"
                    theme="red"
                    @click.prevent="state.image = ''"
                    tooltip="Remove Image"
                  />
                </div>
              </template>
            </FileUploader>
          </div>
          <template v-for="field in fields" :key="field.key">
            <FormControl
              :class="[
                '[&_p]:text-p-xs',
                field.type === 'select' && '[&_[data-slot=trigger]]:w-full',
              ]"
              v-if="field.type !== 'Link'"
              :key="field.key"
              :type="field.type"
              :label="field.label"
              :required="field.required"
              :placeholder="field.placeholder"
              :description="field.description"
              :options="field.options"
              v-model="state[field.key]"
            >
              <template #prefix>
                <component :is="field.prefix" />
              </template>
            </FormControl>
            <Link
              v-else
              :label="field.label"
              :placeholder="field.placeholder"
              :description="field.description"
              v-model="state[field.key]"
              :doctype="field.doctype"
              :required="field.required"
            >
              <template #prefix>
                <component :is="field.prefix" />
              </template>
            </Link>
          </template>

          <div class="border-t border-outline-gray-2 pt-4 space-y-4">
            <h3 class="text-base font-medium text-ink-gray-8">
              {{ __("Primary Contact Details") }}
            </h3>
            <div class="grid grid-cols-2 gap-4">
              <FormControl
                class="[&_p]:text-p-xs"
                type="text"
                :label="__('First Name')"
                v-model="primaryContact.firstName"
              />
              <FormControl
                class="[&_p]:text-p-xs"
                type="text"
                :label="__('Last Name')"
                v-model="primaryContact.lastName"
              />
            </div>
            <FormControl
              class="[&_p]:text-p-xs"
              type="email"
              :label="__('Email Id')"
              v-model="primaryContact.email"
            />
            <PhoneControl
              :label="__('Mobile Number')"
              v-model="primaryContact.mobileNo"
            />
          </div>

          <div class="float-right flex space-x-2">
            <Button
              label="Add"
              theme="gray"
              variant="solid"
              :loading="customerResource.loading"
              @click.prevent="addCustomer"
            />
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import {
  customerFields as fields,
  useNewCustomerForm,
} from "@/composables/customer";
import { __ } from "@/translation";
import type { File, Resource } from "@/types";
import { getErrorMessage, validateEmailWithZod } from "@/utils";
import {
  Avatar,
  Button,
  Dialog,
  FileUploader,
  FormControl,
  createResource,
  toast,
} from "frappe-ui";
import { useRouter } from "vue-router";
import Link from "../frappe-ui/Link.vue";
import PhoneControl from "../frappe-ui/PhoneControl/PhoneControl.vue";
import { OrganizationsIcon } from "../icons";

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
