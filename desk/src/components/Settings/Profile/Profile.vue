<template>
  <SettingsLayoutBase
    :title="__('Profile')"
    :description="__('Manage your profile information.')"
  >
    <template #content>
      <div class="flex items-center justify-between gap-2 pt-1.5 pb-8">
        <FileUploader
          :fileTypes="['image/*']"
          @success="
            (file) => {
              updateImage(file.file_url);
            }
          "
        >
          <template #default="{ openFileSelector, error: _error, uploading }">
            <div class="flex items-center justify-center gap-2">
              <div class="group relative !size-14">
                <Avatar
                  class="!size-14"
                  :image="user.doc.user_image"
                  :label="fullName"
                />
                <Tooltip
                  :hoverDelay="0"
                  placement="bottom"
                  :text="profileTooltipText"
                >
                  <div
                    class="z-1 absolute top-0 left-0 flex h-9 cursor-pointer items-center justify-center rounded-full !size-14"
                    @click.stop="openFileSelector"
                  />
                  <div
                    v-if="user.doc.user_image"
                    class="z-1 size-4 absolute -top-1 -right-1 flex cursor-pointer items-center justify-center rounded-full bg-surface-white opacity-0 duration-300 ease-in-out group-hover:opacity-100 hover:bg-surface-gray-2 outline outline-black-overlay-50"
                    @click.stop="updateImage()"
                    @mouseenter="isHoveringRemove = true"
                    @mouseleave="isHoveringRemove = false"
                  >
                    <FeatherIcon
                      name="x"
                      class="size-3.5 cursor-pointer text-ink-gray-4"
                    />
                  </div>
                </Tooltip>
                <div
                  v-if="uploading"
                  class="w-full h-full top-0 left-0 absolute bg-black bg-opacity-20 rounded-full flex items-center justify-center"
                >
                  <LoadingIndicator class="size-4" />
                </div>
              </div>
              <div class="flex flex-col gap-1">
                <div class="flex flex-col gap-1">
                  <div v-if="!editName" class="flex items-end gap-1">
                    <span
                      class="text-lg sm:text-xl !font-semibold text-ink-gray-8"
                    >
                      {{ user?.doc?.full_name }}
                    </span>
                    <Button
                      class="!px-1 !h-5"
                      variant="ghost"
                      @click="editFullName"
                    >
                      <EditIcon class="size-3.5" />
                    </Button>
                  </div>
                  <div v-else class="flex items-center gap-1">
                    <TextInput
                      ref="fullNameRef"
                      v-model="fullName"
                      @keydown.enter="save"
                      @keydown.esc.stop="editName = false"
                    />
                    <Button variant="outline" icon="check" @click="save" />
                  </div>
                  <span class="text-p-sm text-ink-gray-6">
                    {{ user?.doc?.email }}
                  </span>
                </div>
                <ErrorMessage :message="__(_error)" />
              </div>
            </div>
          </template>
        </FileUploader>
      </div>
      <div>
        <div class="flex items-center justify-between">
          <div class="flex gap-2 items-center">
            <div class="text-base font-semibold text-ink-gray-9">
              {{ __("Account Info & Security") }}
            </div>
            <Badge
              v-if="isProfileDirty"
              :variant="'subtle'"
              :theme="'orange'"
              size="sm"
              :label="__('Unsaved')"
            />
          </div>
        </div>
        <div class="flex items-center justify-between mt-6">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __("Emails & Signature") }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  "Manage your account emails and email signature for communication."
                )
              }}
            </span>
          </div>
          <Button
            :label="__('Configure')"
            @click="emit('updateStep', 'user-email-settings')"
          />
        </div>
        <div class="flex items-center justify-between mt-6">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __("Password") }}
            </span>
            <span class="text-p-sm text-ink-gray-6">{{
              __("Change your account password for security.")
            }}</span>
          </div>
          <Button
            icon-left="lock"
            :label="__('Change Password')"
            @click="showChangePasswordModal = true"
          />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <ChangePasswordModal
    v-if="showChangePasswordModal"
    v-model="showChangePasswordModal"
  />
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch, useTemplateRef } from "vue";
import {
  Avatar,
  Badge,
  Button,
  FileUploader,
  LoadingIndicator,
  toast,
  createDocumentResource,
} from "frappe-ui";
import { __ } from "@/translation";
import { useAuthStore } from "@/stores/auth";
import EditIcon from "~icons/lucide/edit";
const emit = defineEmits(["updateStep"]);

import ChangePasswordModal from "./components/ChangePasswordModal.vue";
import { disableSettingModalOutsideClick } from "../settingsModal";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
const showChangePasswordModal = ref(false);

const { userId } = useAuthStore();
const user = createDocumentResource({ doctype: "User", name: userId });

const isHoveringRemove = ref(false);
const editName = ref(false);

const profileTooltipText = computed(() => {
  if (isHoveringRemove.value) return __("Remove Photo");
  return user.doc.user_image ? __("Change Photo") : __("Upload Photo");
});

const fullNameRef = useTemplateRef("fullNameRef");
const fullName = computed({
  get: () => {
    return user.doc.full_name;
  },
  set: (val) => {
    const [firstName, ...lastName] = val.split(" ");
    user.doc.first_name = firstName;
    user.doc.last_name = lastName.join(" ");
  },
});

function editFullName() {
  editName.value = true;
  nextTick(() => fullNameRef.value?.el?.focus());
}

const isDirty = computed(() => {
  return JSON.stringify(user.doc) !== JSON.stringify(user.originalDoc);
});

function save() {
  if (!isDirty.value) {
    editName.value = false;
    return;
  }

  user.save.submit(null, {
    onSuccess: () => {
      editName.value = false;
      toast.success(__("Profile Updated Successfully"));
    },
    onError: (err: { message: string; messages: string[] }) => {
      toast.error(err.message + ": " + err.messages[0]);
    },
  });
}

function updateImage(fileUrl = "") {
  isHoveringRemove.value = false;
  user.doc.user_image = fileUrl;
  save();
}

watch(isDirty, (val) => {
  disableSettingModalOutsideClick.value = val;
});
</script>
