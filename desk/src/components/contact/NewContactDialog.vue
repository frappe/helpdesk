<template>
  <div>
    <Dialog
      v-model:open="open"
      :title="__('Create Contact')"
      size="md"
      @after-leave="reset"
    >
      <template #default>
        <div class="space-y-4">
          <template
            v-for="fieldOrRow in fieldConfig"
            :key="
              Array.isArray(fieldOrRow) ? fieldOrRow[0]?.key : fieldOrRow.key
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
              <ImageAvatar
                v-model="state.image"
                :label="__('Photo')"
                :fallback-label="state.firstName || __('Contact')"
                shape="circle"
              />
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
              <PhoneControl :label="fieldOrRow.label" v-model="state.phone" />
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

          <Checkbox
            size="sm"
            v-model="state.invite"
            :label="__('Invite as User')"
          />

          <div class="flex justify-end pt-1 gap-2">
            <Button
              label="Create"
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
import ImageAvatar from "@/components/ImageAvatar.vue";
import { useNewContact } from "@/composables/contact";
import { __ } from "@/translation";
import { Button, Checkbox, Dialog, FormControl } from "frappe-ui";
import LucideMail from "~icons/lucide/mail";
import Link from "../frappe-ui/Link.vue";
import PhoneControl from "../frappe-ui/PhoneControl/PhoneControl.vue";

const open = defineModel<boolean>({ default: false });

const { state, fieldConfig, addContact, isLoading, reset } = useNewContact();

function handleAdd() {
  addContact();
}
</script>
