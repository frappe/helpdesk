<template>
  <Dialog
    v-model="open"
    :options="{ size: 'md' }"
    :disableOutsideClickToClose="isDirty"
  >
    <template #body>
      <div class="bg-surface-modal px-4 py-5 sm:px-6">
        <div class="mb-6 flex items-center justify-between">
          <div class="flex items-center gap-1">
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __("Edit Contact") }}
            </h3>
            <Badge
              v-if="isDirty"
              :label="__('Unsaved')"
              variant="subtle"
              theme="orange"
            />
          </div>
          <Button icon="x" variant="ghost" @click="open = false" />
        </div>

        <div class="space-y-4">
          <!-- Avatar -->
          <div class="flex gap-4 items-center">
            <Avatar
              v-if="state.image"
              :image="state.image"
              :label="
                `${state.firstName} ${state.lastName}`.trim() || 'Contact'
              "
              shape="circle"
              size="3xl"
            />
            <div
              v-else
              class="flex size-12 items-center justify-center rounded-full bg-surface-gray-2 text-2xl font-medium uppercase text-ink-gray-5 select-none"
            >
              <LucideUser class="size-8" />
            </div>
            <FileUploader
              :fileTypes="['image/*']"
              @success="(file: FileType) => (state.image = file.file_url)"
            >
              <template #default="{ openFileSelector }">
                <div class="space-x-2">
                  <Button
                    variant="subtle"
                    :label="
                      state.image ? __('Replace picture') : __('Upload picture')
                    "
                    @click.prevent="openFileSelector()"
                  />
                  <Button
                    v-if="state.image"
                    :label="__('Remove')"
                    variant="subtle"
                    theme="red"
                    @click.prevent="state.image = ''"
                  />
                </div>
              </template>
            </FileUploader>
          </div>

          <!-- First + Last name -->
          <div class="grid grid-cols-2 gap-4">
            <FormControl
              class="[&_p]:text-p-xs"
              :label="__('First Name')"
              type="text"
              :required="true"
              :placeholder="__('John')"
              v-model="state.firstName"
            />
            <FormControl
              class="[&_p]:text-p-xs"
              :label="__('Last Name')"
              type="text"
              :placeholder="__('Doe')"
              v-model="state.lastName"
            />
          </div>

          <!-- Email IDs -->
          <div class="space-y-1.5">
            <label class="text-xs text-ink-gray-5">
              {{ __("Email") }}
              <span class="text-ink-red-3">*</span>
            </label>
            <ContactInputRow
              v-for="(email, index) in state.emails"
              :key="email.key"
              v-model="email.email_id"
              type="email"
              placeholder="name@example.com"
              :isPrimary="email.isPrimary"
              :canRemove="!email.isPrimary"
              :autofocus="email.key === autofocusKey"
              @setPrimary="setPrimary('email', index)"
              @remove="removeRow('email', index)"
            />
            <Button
              key="add-email"
              size="sm"
              :label="__('Add Email')"
              @click="addRow('email')"
            >
              <template #prefix>
                <LucidePlus class="size-3.5" />
              </template>
            </Button>
          </div>

          <!-- Phone numbers -->
          <div class="space-y-1.5 flex flex-col items-start w-full flex-1">
            <label class="text-xs text-ink-gray-5">{{ __("Phone") }}</label>
            <ContactInputRow
              v-for="(phone, index) in state.phones"
              :key="phone.key"
              v-model="phone.phone"
              type="tel"
              placeholder="+1 234 567 8900"
              :isPrimary="phone.isPrimary"
              :canRemove="true"
              :autofocus="phone.key === autofocusKey"
              @setPrimary="setPrimary('phone', index)"
              @remove="removeRow('phone', index)"
            />
            <Button
              key="add-phone"
              size="sm"
              :label="__('Add Phone')"
              @click="addRow('phone')"
            >
              <template #prefix>
                <LucidePlus class="size-3.5" />
              </template>
            </Button>
          </div>

          <!-- Timezone -->
          <TimezoneControl
            :label="__('Timezone')"
            v-model="state.timezone"
            v-if="doc.doc?.user"
          />

          <!-- Save -->
          <div class="flex justify-end">
            <Button
              :label="__('Save')"
              variant="solid"
              theme="gray"
              :disabled="!isDirty"
              :loading="editContactResource.loading"
              @click="handleSave"
            />
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { nextEntryKey, useContact } from "@/composables/contact";
import { __ } from "@/translation";
import type { File as FileType } from "@/types";
import {
  Avatar,
  Badge,
  Button,
  Dialog,
  FileUploader,
  FormControl,
} from "frappe-ui";
import { ref } from "vue";
import LucidePlus from "~icons/lucide/plus";
import LucideUser from "~icons/lucide/user";
import TimezoneControl from "../TimezoneControl.vue";
import ContactInputRow from "./ContactInputRow.vue";

const props = defineProps<{ name: string }>();
const open = defineModel<boolean>({ default: false });

const { state, parseContactData, isDirty, editContactResource, doc } =
  useContact(props.name);

const autofocusKey = ref<number | null>(null);

function addRow(type: "email" | "phone") {
  const key = nextEntryKey();
  if (type === "email") {
    state.emails.push({
      email_id: "",
      isPrimary: state.emails.length === 0,
      key,
    });
  } else {
    state.phones.push({
      phone: "",
      isPrimary: false,
      key,
    });
  }
  autofocusKey.value = key;
}

function removeRow(type: "email" | "phone", index: number) {
  const list = type === "email" ? state.emails : state.phones;
  if (type === "phone" && list.length === 1) {
    const row = state.phones[0];
    if (row) {
      row.phone = "";
      row.isPrimary = false;
    }
    return;
  }
  const wasPrimary = list[index]?.isPrimary;
  list.splice(index, 1);
  if (type === "email") {
    const first = list[0];
    if (wasPrimary && first) {
      first.isPrimary = true;
    }
  }
}

function setPrimary(type: "email" | "phone", index: number) {
  if (type === "email") {
    state.emails.forEach((e, i) => {
      e.isPrimary = i === index;
    });
  } else {
    state.phones.forEach((p, i) => {
      p.isPrimary = i === index;
    });
  }
}

async function handleSave() {
  if (!isDirty.value && doc.getInfo?.data?.timezone === state.timezone) return;
  editContactResource.submit(
    {
      name: props.name,
      doc: parseContactData(),
    },
    {
      onSuccess: () => {
        open.value = false;
        doc.reload();
        doc.getInfo.reload();
      },
    }
  );
}
</script>

<style scoped>
.row-leave-active {
  position: absolute;
  width: 100%;
  transition: opacity 180ms cubic-bezier(0.2, 0, 0, 1),
    transform 180ms cubic-bezier(0.2, 0, 0, 1);
}
.row-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
