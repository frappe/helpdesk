<template>
  <Dialog :options="options">
    <template #body-main>
      <div class="flex flex-col items-center gap-4 p-6">
        <div class="text-xl font-medium text-gray-900">
          {{ contact.doc?.full_name }}
        </div>
        <Avatar
          size="2xl"
          :label="contact.doc?.full_name"
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
          <Button
            v-if="!contact.doc?.user && isManager"
            label="Invite as user"
            @click="inviteContact"
            :loading="isLoading"
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
          <div class="space-y-1">
            <div class="text-xs">Customer</div>
            <Link
              doctype="HD Customer"
              class="form-control flex-1"
              placeholder="Link to a customer"
              v-model="selectedCustomer"
              :hide-me="true"
            />
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import {
  Avatar,
  call,
  createDocumentResource,
  createListResource,
  Dialog,
  FileUploader,
  toast,
} from "frappe-ui";
import { useOnboarding } from "frappe-ui/frappe";
import type { Ref } from "vue";
import { computed, ref } from "vue";
import zod from "zod";

import Link from "@/components/frappe-ui/Link.vue";
import MultiSelect from "@/components/MultiSelect.vue";
import { useAuthStore } from "@/stores/auth";
import { AutoCompleteItem, File } from "@/types";

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
      toast.error("At least one email is required");
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

const selectedCustomer = computed({
  get() {
    const customerLink = contact.doc?.links?.find(
      (link) => link.link_doctype === "HD Customer"
    );
    return customerLink?.link_name || null;
  },
  set(value) {
    const currentCustomer = contact.doc?.links?.find(
      (link) => link.link_doctype === "HD Customer"
    )?.link_name;

    if (value !== currentCustomer) {
      if (value) {
        const existingCustomerLinkIndex = contact.doc.links?.findIndex(
          (link) => link.link_doctype === "HD Customer"
        );
        if (existingCustomerLinkIndex !== -1) {
          contact.doc.links[existingCustomerLinkIndex].link_name = value;
        } else {
          contact.doc.links.push({
            link_doctype: "HD Customer",
            link_name: value,
          });
        }
      } else {
        contact.doc.links = contact.doc.links?.filter(
          (link) => link.link_doctype !== "HD Customer"
        );
      }
      isDirty.value = true;
    }
  },
});

const customerResource = createListResource({
  doctype: "HD Customer",
  fields: ["name"],
  cache: "customers",
  transform: (data) => {
    return data.map((option) => ({
      label: option.name,
      value: option.name,
    }));
  },
  auto: true,
});

function handleCustomerChange(item: AutoCompleteItem | null) {
  if (!item || item.label === "No label") {
    selectedCustomer.value = null;
  } else {
    selectedCustomer.value = item.value;
  }
}

const { updateOnboardingStep } = useOnboarding("helpdesk");
const { isManager } = useAuthStore();

const contact = createDocumentResource({
  doctype: "Contact",
  name: props.name,
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
    toast.error("No changes to save");
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
    links: contact.doc.links,
  });
  isDirty.value = false;
  emit("contactUpdated");
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
    toast.error("Invalid file type, only PNG and JPG images are allowed");
    return "Invalid file type, only PNG and JPG images are allowed";
  }
}

const isLoading = ref(false);
async function inviteContact(): Promise<void> {
  try {
    isLoading.value = true;
    const user = await call(
      "frappe.contacts.doctype.contact.contact.invite_user",
      {
        contact: contact.doc.name,
      }
    );
    toast.success("Contact invited successfully");
    await contact.setValue.submit({
      user: user,
    });
    updateOnboardingStep("add_invite_contact");
  } catch (error) {
    isLoading.value = false;
    const parser = new DOMParser();
    const doc = parser.parseFromString(
      error.messages?.[0] || error.message,
      "text/html"
    );

    const errMsg = doc.body.innerText;
    toast.error(errMsg);
  } finally {
    isLoading.value = false;
  }
}
</script>
