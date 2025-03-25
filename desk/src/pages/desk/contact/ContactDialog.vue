<template>
  <Dialog :options="options">
    <template #body-main>
      <div class="flex flex-col items-center gap-4 p-6">
        <div class="text-xl font-medium text-gray-900">
          {{ contact.doc?.name }}
        </div>
        <Avatar
          size="2xl"
          :label="contact.doc?.name"
          :image="contact.doc?.image"
          class="cursor-pointer hover:opacity-80"
        />
        <div class="flex gap-2">
          <FileUploader
            :validate-file="validateFile"
            @success="(file:File) => updateImage(file)"
          >
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
import { computed, ref } from "vue";
import type { Ref } from "vue";
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
import { File, AutoCompleteItem } from "@/types";

interface Props {
  name: {
    type: string;
    required: true;
  };
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (event: "contactUpdated"): void;
}>();

interface Email {
  email_id: string;
  is_primary?: boolean;
}

interface Phone {
  phone: string;
  is_primary_phone?: boolean;
  is_primary_mobile?: boolean;
}

const isDirty: Ref<boolean> = ref(false);

const emails = computed({
  get() {
    const emails = contact.doc?.email_ids || [];
    return emails.map((e: Email) => ({
      label: e.email_id,
      value: e.email_id,
    }));
  },
  set(newVal) {
    if (newVal.length === 0) {
      createToast({
        title: "At least one email is required",
        icon: "x",
        iconClasses: "text-red-600",
      });
      return;
    }
    if (newVal.length !== contact.doc.email_ids.length) {
      isDirty.value = true;
    }
    contact.doc.email_ids = newVal.map((email: AutoCompleteItem) => ({
      email_id: email.value,
    }));
  },
});

const phones = computed({
  get() {
    const phone_nos = contact.doc?.phone_nos || [];
    return phone_nos.map((e: Phone) => ({
      label: e.phone,
      value: e.phone,
    }));
  },
  set(newVal) {
    if (newVal.length !== contact.doc.phone_nos.length) {
      isDirty.value = true;
    }
    contact.doc.phone_nos = newVal.map((item: AutoCompleteItem) => ({
      phone: item.value,
    }));
  },
});

const contact = createDocumentResource({
  doctype: "Contact",
  name: props.name,
  cache: [`contact-${props.name}`, props.name],
  auto: true,
  setValue: {
    onSuccess() {
      emit("contactUpdated");
    },
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

function update(): void {
  if (!isDirty.value) {
    createToast({
      title: "No changes to save",
      icon: "x",
      iconClasses: "text-red-600",
    });
    return;
  }
  contact.setValue.submit({
    email_ids: emails.value.map((email: AutoCompleteItem) => ({
      email_id: email.value,
      is_primary: email.value === contact.doc.email_id,
    })),
    phone_nos: phones.value.map((phoneNum: AutoCompleteItem) => ({
      phone: phoneNum.value,
      is_primary_phone: phoneNum.value === contact.doc.phone,
      is_primary_mobile: phoneNum.value === contact.doc.phone,
    })),
  });
}

function updateImage(file: File): void {
  contact.setValue.submit({
    image: file?.file_url || null,
  });
  isDirty.value = true;
}

function validateEmail(input: AutoCompleteItem): string | void {
  const success = zod.string().email().safeParse(input.value).success;
  if (!success) return "Invalid email";
}

function validatePhone(input: AutoCompleteItem): string | void {
  const success = zod
    .string()
    .regex(/^\+[1-9]\d{1,14}$/)
    .min(10)
    .max(15)
    .safeParse(input.value).success;
  if (!success) return "Invalid phone number";
}

function validateFile(file: File): string | void {
  let extn = file.name.split(".").pop().toLowerCase();
  if (!["png", "jpg", "jpeg"].includes(extn)) {
    createToast({
      title: "Invalid file type, only PNG and JPG images are allowed",
      icon: "x",
      iconClasses: "text-red-600",
    });
    return "Invalid file type, only PNG and JPG images are allowed";
  }
}
</script>
