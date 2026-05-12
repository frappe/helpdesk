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
              {{ __("Edit contact") }}
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
                      state.image === doc.doc.image
                        ? __('Upload picture')
                        : __('Replace picture')
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
          <div class="space-y-2">
            <label class="text-xs text-ink-gray-5">
              {{ __("Email") }}
              <span class="text-ink-red-3">*</span>
            </label>
            <div
              v-for="(email, index) in state.emails"
              :key="index"
              class="flex items-center gap-1"
            >
              <FormControl
                class="[&_p]:text-p-xs flex-1"
                type="email"
                :placeholder="`john.doe${
                  index > 0 ? `+${index}` : ''
                }@example.com`"
                v-model="email.email_id"
              />
              <Tooltip :text="__('Primary contact')">
                <button
                  type="button"
                  class="p-1 shrink-0"
                  @click="setPrimary('email', index)"
                >
                  <LucideStar
                    class="size-4"
                    :class="
                      email.isPrimary
                        ? 'fill-ink-amber-2 text-ink-amber-2'
                        : 'text-ink-gray-3 hover:text-ink-gray-5'
                    "
                  />
                </button>
              </Tooltip>
              <button
                v-if="index > 0"
                type="button"
                class="p-1 shrink-0 text-ink-gray-3 hover:text-ink-red-3"
                @click="removeRow('email', index)"
              >
                <LucideTrash2 class="size-4" />
              </button>
            </div>
            <Button variant="subtle" size="sm" @click="addRow('email')">
              <template #prefix>
                <LucidePlus class="size-3.5" />
              </template>
              {{ __("Add email address") }}
            </Button>
          </div>

          <!-- Phone numbers -->
          <div class="flex flex-col gap-y-2">
            <label class="text-xs text-ink-gray-5">{{ __("Phone") }}</label>
            <div
              v-for="(phone, index) in state.phones"
              :key="index"
              class="flex items-center gap-1"
            >
              <FormControl
                class="[&_p]:text-p-xs flex-1"
                type="tel"
                :placeholder="`+1 234 567 89${index > 0 ? `${index}` : 0}`"
                v-model="phone.phone"
              >
              </FormControl>
              <Tooltip :text="__('Primary contact')">
                <button
                  type="button"
                  class="p-1 shrink-0"
                  @click="setPrimary('phone', index)"
                >
                  <LucideStar
                    class="size-4"
                    :class="
                      phone.isPrimary
                        ? 'fill-ink-amber-2 text-ink-amber-2'
                        : 'text-ink-gray-3 hover:text-ink-gray-5'
                    "
                  />
                </button>
              </Tooltip>
              <button
                type="button"
                class="p-1 shrink-0 text-ink-gray-3 hover:text-ink-red-3"
                @click="removeRow('phone', index)"
              >
                <LucideTrash2 class="size-4" />
              </button>
            </div>
            <Button
              variant="subtle"
              size="sm"
              @click="addRow('phone')"
              class="w-fit"
            >
              <template #prefix>
                <LucidePlus class="size-3.5" />
              </template>
              {{ __("Add number") }}
            </Button>
          </div>

          <!-- Timezone -->
          <TimezoneControl :label="__('Timezone')" v-model="state.timezone" />

          <!-- Save -->
          <div class="flex justify-end">
            <Button
              :label="__('Save')"
              variant="solid"
              theme="gray"
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
import { useContact } from "@/composables/contact";
import { __ } from "@/translation";
import type { File as FileType } from "@/types";
import {
  Avatar,
  Badge,
  Button,
  Dialog,
  FileUploader,
  FormControl,
  Tooltip,
} from "frappe-ui";
import LucidePlus from "~icons/lucide/plus";
import LucideStar from "~icons/lucide/star";
import LucideTrash2 from "~icons/lucide/trash-2";
import LucideUser from "~icons/lucide/user";
import TimezoneControl from "../TimezoneControl.vue";

const props = defineProps<{ name: string }>();
const open = defineModel<boolean>({ default: false });

const { state, parseContactData, isDirty, editContactResource, doc } =
  useContact(props.name);

function addRow(type: "email" | "phone") {
  if (type === "email") {
    state.emails.push({ email_id: "", isPrimary: false });
  } else {
    state.phones.push({ phone: "", isPrimary: false });
  }
}

function removeRow(type: "email" | "phone", index: number) {
  if (type === "email") {
    state.emails.splice(index, 1);
  } else {
    state.phones.splice(index, 1);
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
  debugger;
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
