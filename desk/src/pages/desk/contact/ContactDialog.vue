<template>
  <Dialog :options="options">
    <template #body-main>
      <div class="flex flex-col items-center gap-4 p-6">
        <div class="text-xl font-medium text-gray-900">
          {{ contact.doc?.name }}
        </div>
        <Avatar
          size="lg"
          :label="contact.doc?.name"
          :image="contact.doc?.image"
          class="cursor-pointer hover:opacity-80"
        />
        <div class="flex gap-2">
          <FileUploader @success="(file) => updateImage(file)">
            <template #default="{ uploading, openFileSelector }">
              <Button
                :label="contact.doc?.image ? 'Change photo' : 'Upload photo'"
                :loading="uploading"
                @click="openFileSelector"
              />
            </template>
          </FileUploader>
          <Button
            v-if="contact.doc?.image"
            label="Remove photo"
            @click="updateImage(null)"
          />
        </div>
        <div class="w-full space-y-2 text-sm text-gray-700">
          <div class="space-y-1">
            <div class="text-xs">Emails</div>
            <MultiSelect
              v-model:items="emails"
              placeholder="john.doe@example.com"
              :validate="validateEmail"
            />
          </div>
          <div class="space-y-1">
            <div class="text-xs">Phone Nos</div>
            <MultiSelect
              v-model:items="phones"
              placeholder="+91 98765 43210"
              :validate="validatePhone"
            />
          </div>
        </div>
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
import zod from "zod";
import { createToast } from "@/utils";
import { useError } from "@/composables/error";
import MultiSelect from "@/components/MultiSelect.vue";

const props = defineProps({
  name: {
    type: String,
    required: true,
  },
});

const emails = computed({
  get() {
    const l = contact.doc?.email_ids || [];
    return l.map((e) => ({
      label: e.email_id,
      value: e.email_id,
    }));
  },
  set(e) {
    contact.doc.email_ids = e.map((item) => ({
      email_id: item.value,
    }));
  },
});

const phones = computed({
  get() {
    const l = contact.doc?.phone_nos || [];
    return l.map((e) => ({
      label: e.phone,
      value: e.phone,
    }));
  },
  set(e) {
    contact.doc.phone_nos = e.map((item) => ({
      phone: item.value,
    }));
  },
});

const contact = createDocumentResource({
  doctype: "Contact",
  name: props.name,
  auto: true,
  setValue: {
    onSuccess() {
      createToast({
        title: "Contact updated",
        icon: "check",
        iconClasses: "text-green-500",
      });
    },
    onError: useError({ title: "Error updating contact" }),
  },
});

const options = computed(() => ({
  title: contact.doc?.name,
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
  contact.setValue.submit({
    email_ids: emails.value.map((item) => ({
      email_id: item.value,
      is_primary: item.value === contact.doc.email_id,
    })),
    phone_nos: phones.value.map((item) => ({
      phone: item.value,
      is_primary_phone: item.value === contact.doc.phone,
      is_primary_mobile: item.value === contact.doc.phone,
    })),
  });
}

function updateImage(file) {
  contact.setValue.submit({
    image: file?.file_url || null,
  });
}

function validateEmail(input) {
  const success = zod.string().email().safeParse(input.value).success;
  if (!success) return "Invalid email";
}

function validatePhone(input) {
  const success = zod
    .string()
    .regex(/^\+[1-9]\d{1,14}$/)
    .min(10)
    .max(15)
    .safeParse(input.value).success;
  if (!success) return "Invalid phone number";
}
</script>
