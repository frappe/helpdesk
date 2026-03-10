<template>
  <div>
    <Dialog
      v-model="model"
      :options="{ title: __('New Customer'), size: 'md' }"
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
              class="flex size-12 items-center justify-center bg-surface-gray-2 uppercase text-ink-gray-5 select-none font-medium text-2xl rounded-full"
              v-else
            >
              <OrganizationsIcon class="size-8" />
            </div>
            <FileUploader
              :fileTypes="['image/*']"
              @success="(file) => (state.image = file.file_url)"
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
                    label="Remove Picture"
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
              class="[&_p]:text-p-xs"
              v-if="field.type !== 'Link'"
              :key="field.key"
              :label="field.label"
              :required="field.required"
              :placeholder="field.placeholder"
              :description="field.description"
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
            </Link>
          </template>

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
import { customerFields as fields, useCustomer } from "@/composables/customer";
import { __ } from "@/translation";
import type { Resource } from "@/types";
import {
  Avatar,
  Button,
  Dialog,
  FileUploader,
  FormControl,
  createResource,
  toast,
} from "frappe-ui";
import { Link } from "frappe-ui/frappe";
import { useRouter } from "vue-router";
import { OrganizationsIcon } from "../icons";

const model = defineModel<boolean>({ default: false });
const router = useRouter();

const { state } = useCustomer();

const customerResource: Resource = createResource({
  url: "frappe.client.insert",
  method: "POST",
  onSuccess: (data: { name: string }) => {
    router.push({ name: "Customer", params: { id: data.name } });
    toast.success(__("Customer created"));
  },
});

function addCustomer() {
  customerResource.submit({
    doc: {
      doctype: "HD Customer",
      customer_name: state.name,
      domain: state.domain,
      image: state.image,
      country: state.country,
    },
  });
}
</script>
