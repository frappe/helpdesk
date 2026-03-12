<template>
  <Dialog
    v-model="model"
    :options="{ title: __('Edit Customer'), size: 'md' }"
    :disableOutsideClickToClose="isDirty()"
    @after-leave="revertChanges"
  >
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 py-5 sm:px-6">
        <div class="mb-6 flex items-center justify-between">
          <div class="flex items-center gap-1">
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              Edit Customer
            </h3>
            <Badge
              v-if="isDirty()"
              label="Unsaved"
              variant="subtle"
              theme="orange"
            />
          </div>
          <Button icon="x" @click="model = false" variant="ghost" />
        </div>
        <div class="space-y-4">
          <!-- Image section -->
          <div class="flex gap-4 items-center">
            <Avatar
              v-if="state.image"
              :image="state.image"
              :label="state.name || 'Customer'"
              shape="circle"
              size="3xl"
            />
            <div
              v-else
              class="flex size-12 items-center justify-center bg-surface-gray-2 uppercase text-ink-gray-5 select-none font-medium text-2xl rounded-full"
            >
              <OrganizationsIcon class="size-8" />
            </div>
            <FileUploader
              :fileTypes="['image/*']"
              @success="(file: { file_url: string }) => onImageUpload(file)"
            >
              <template #default="{ openFileSelector, uploading }">
                <div class="space-x-2">
                  <Button
                    variant="subtle"
                    label="Upload Image"
                    :loading="uploading"
                    @click.prevent="openFileSelector()"
                  />
                  <Button
                    v-if="state.image"
                    label="Remove Image"
                    variant="subtle"
                    theme="red"
                    @click.prevent="onImageRemove()"
                  />
                </div>
              </template>
            </FileUploader>
          </div>

          <!-- Fields -->
          <template v-for="field in customerFields" :key="field.key">
            <FormControl
              class="[&_p]:text-p-xs"
              v-if="field.type !== 'Link'"
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
              :doctype="field.doctype"
              :required="field.required"
              v-model="state[field.key]"
            >
              <template #prefix>
                <component :is="field.prefix" />
              </template>
            </Link>
          </template>

          <div class="float-right flex space-x-2 pb-5">
            <Button
              label="Save"
              theme="gray"
              variant="solid"
              :loading="customer.setValue.loading"
              @click.prevent="save"
            />
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { customerFields, useCustomer } from "@/composables/customer";
import { __ } from "@/translation";
import { CustomerResourceSymbol } from "@/types";
import {
  Avatar,
  Badge,
  Button,
  Dialog,
  FileUploader,
  FormControl,
  toast,
} from "frappe-ui";
import { inject } from "vue";
import Link from "../frappe-ui/Link.vue";
import { OrganizationsIcon } from "../icons";

const model = defineModel<boolean>({ default: false });
const emit = defineEmits(["update"]);

const customer = inject(CustomerResourceSymbol)!;
const { state, isDirty } = useCustomer(null, customer);

async function save() {
  await customer.setValue.submit({
    customer_name: state.name,
    domain: state.domain,
    country: state.country,
    image: state.image,
  });
  toast.success(__("Customer updated"));
  emit("update");
  model.value = false;
}

// Image saves immediately; all other fields wait for Save button
function onImageUpload(file: { file_url: string }) {
  state.image = file.file_url;
}

function onImageRemove() {
  state.image = "";
}

function revertChanges() {
  if (!isDirty()) return;
  state.name = customer.doc.customer_name || "";
  state.domain = customer.doc.domain || "";
  state.country = customer.doc.country || "";
  state.image = customer.doc.image || "";
}
</script>
