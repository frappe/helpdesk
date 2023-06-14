<template>
  <Dialog :options="options">
    <template #body-main>
      <div class="flex flex-col items-center gap-4 p-6">
        <div class="text-xl font-medium text-gray-900">
          {{ customer.doc?.name }}
        </div>
        <Avatar
          size="lg"
          :label="customer.doc?.name"
          :image="customer.doc?.image"
          class="cursor-pointer hover:opacity-80"
        />
        <div class="flex gap-2">
          <FileUploader @success="(file) => updateImage(file)">
            <template #default="{ uploading, openFileSelector }">
              <Button
                label="Change photo"
                :loading="uploading"
                @click="openFileSelector"
              />
            </template>
          </FileUploader>
          <Button label="Remove photo" @click="updateImage(null)" />
        </div>
        <form class="w-full" @submit.prevent="update">
          <Input v-model="domain" label="Domain" placeholder="example.com" />
        </form>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";
import {
  createDocumentResource,
  Avatar,
  Dialog,
  FileUploader,
} from "frappe-ui";
import { createToast } from "@/utils/toasts";

const props = defineProps({
  name: {
    type: String,
    required: true,
  },
});

const domain = computed({
  get() {
    return customer.doc?.domain;
  },
  set(d: string) {
    customer.doc.domain = d;
  },
});

const customer = createDocumentResource({
  doctype: "HD Customer",
  name: props.name,
  auto: true,
  setValue: {
    onSuccess() {
      createToast({
        title: "Customer updated",
        icon: "check",
        iconClasses: "text-green-500",
      });
    },
    onError(error) {
      createToast({
        title: "Error updating customer",
        text: error.messages.join(", "),
        icon: "x",
        iconClasses: "text-red-500",
      });
    },
  },
});

const options = computed(() => ({
  title: customer.doc?.name,
  actions: [
    {
      label: "Save",
      theme: "gray",
      variant: "solid",
      onClick: () => update(),
    },
  ],
}));

function update() {
  customer.setValue.submit({
    domain: domain.value,
  });
}

function updateImage(file) {
  customer.setValue.submit({
    image: file?.file_url || null,
  });
}
</script>
