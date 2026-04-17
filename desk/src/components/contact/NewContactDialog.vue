<template>
  <div>
    <Dialog v-model="open" :options="{ title: __('Add Contact'), size: 'md' }">
      <template #body-content>
        <div class="space-y-4">
          <template
            v-for="fieldOrRow in fieldConfig"
            :key="
              Array.isArray(fieldOrRow) ? fieldOrRow[0].key : fieldOrRow.key
            "
          >
            <!-- Grid row (e.g. first + last name) -->
            <div
              v-if="Array.isArray(fieldOrRow)"
              class="grid grid-cols-2 gap-4"
            >
              <template v-for="field in fieldOrRow" :key="field.key">
                <FormControl
                  class="[&_p]:text-p-xs"
                  :label="field.label"
                  :type="field.type"
                  :required="field.required"
                  :placeholder="field.placeholder"
                  v-model="(state as any)[field.key]"
                >
                  <template v-if="field.prefix" #prefix>
                    <component :is="field.prefix" />
                  </template>
                </FormControl>
              </template>
            </div>

            <!-- File: avatar + uploader -->
            <template v-else-if="fieldOrRow.type === 'file'">
              <div class="flex gap-4 items-center">
                <Avatar
                  v-if="state.image"
                  :image="state.image"
                  :label="state.firstName || 'Contact'"
                  shape="circle"
                  size="3xl"
                />
                <div
                  v-else
                  class="flex size-12 items-center justify-center bg-surface-gray-2 uppercase text-ink-gray-5 select-none font-medium text-2xl rounded-full"
                >
                  <UserIcon class="size-8" />
                </div>
                <FileUploader
                  :fileTypes="['image/*']"
                  @success="(file: FileType) => (state.image = file.file_url)"
                >
                  <template #default="{ openFileSelector }">
                    <div class="space-x-2">
                      <Button
                        variant="subtle"
                        label="Upload Image"
                        @click.prevent="openFileSelector()"
                      />
                      <Button
                        v-if="state.image"
                        label="Remove Image"
                        variant="subtle"
                        theme="red"
                        @click.prevent="state.image = ''"
                      />
                    </div>
                  </template>
                </FileUploader>
              </div>
            </template>

            <!-- Email: single flat field -->
            <template v-else-if="fieldOrRow.type === 'email'">
              <FormControl
                class="[&_p]:text-p-xs"
                :label="fieldOrRow.label"
                type="email"
                :required="fieldOrRow.required"
                :placeholder="fieldOrRow.placeholder"
                v-model="state.email"
              >
                <template #prefix>
                  <LucideMail class="size-4" />
                </template>
              </FormControl>
            </template>

            <!-- Phone (tel): single flat field -->
            <template v-else-if="fieldOrRow.type === 'tel'">
              <FormControl
                class="[&_p]:text-p-xs"
                :label="fieldOrRow.label"
                type="text"
                :placeholder="fieldOrRow.placeholder"
                v-model="state.phone"
              >
                <template #prefix>
                  <LucidePhone class="size-4" />
                </template>
              </FormControl>
            </template>

            <template v-else-if="fieldOrRow.type === 'autocomplete'">
              <div class="space-y-1.5">
                <Autocomplete
                  :options="fieldOrRow.options || []"
                  :placeholder="fieldOrRow.placeholder"
                  v-model="state.timezone"
                  :loading="false"
                  :label="fieldOrRow.label"
                />
              </div>
            </template>

            <template v-else-if="fieldOrRow.type === 'Link'">
              <div class="space-y-1.5">
                <Link
                  :doctype="fieldOrRow.doctype!"
                  :placeholder="fieldOrRow.placeholder"
                  v-model="state.customer"
                  :label="fieldOrRow.label"
                />
              </div>
            </template>

            <!-- Default: text / number / etc -->
            <template v-else>
              <FormControl
                class="[&_p]:text-p-xs"
                :label="fieldOrRow.label"
                :type="fieldOrRow.type"
                :required="fieldOrRow.required"
                :placeholder="fieldOrRow.placeholder"
                v-model="(state as any)[fieldOrRow.key]"
              >
                <template v-if="fieldOrRow.prefix" #prefix>
                  <component :is="fieldOrRow.prefix" />
                </template>
              </FormControl>
            </template>
          </template>

          <div class="flex justify-end pt-1">
            <Button
              label="Add"
              theme="gray"
              variant="solid"
              @click="handleAdd"
              :loading="isLoading"
            />
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { useNewContact } from "@/composables/contact";
import { __ } from "@/translation";
import type { File as FileType } from "@/types";
import {
  Autocomplete,
  Avatar,
  Button,
  Dialog,
  FileUploader,
  FormControl,
} from "frappe-ui";
import LucideMail from "~icons/lucide/mail";
import LucidePhone from "~icons/lucide/phone";
import UserIcon from "~icons/lucide/user";
import Link from "../frappe-ui/Link.vue";

const open = defineModel<boolean>({ default: false });

const { state, fieldConfig, addContact, isLoading } = useNewContact();

async function handleAdd() {
  try {
    await addContact();
    open.value = false;
  } catch (error) {
    console.error("Error adding contact:", error);
  }
}
</script>
