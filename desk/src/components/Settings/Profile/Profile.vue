<template>
  <div class="px-10 py-8">
    <SettingsLayoutHeader
      :title="__('Profile')"
      :description="__('Manage your profile information')"
    />
  </div>
  <div class="px-10 pb-8 overflow-y-auto">
    <div class="flex items-center justify-between gap-2">
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
                :image="profile.userImage"
                :label="profile.fullName"
              />
              <component
                :is="profile.userImage ? Dropdown : 'div'"
                v-bind="
                  profile.userImage
                    ? {
                        options: [
                          {
                            icon: 'upload',
                            label: profile.userImage
                              ? __('Change image')
                              : __('Upload image'),
                            onClick: openFileSelector,
                          },
                          {
                            icon: 'trash-2',
                            label: __('Remove image'),
                            onClick: () => updateImage(null),
                          },
                        ],
                      }
                    : { onClick: openFileSelector }
                "
              >
                <div
                  class="z-1 absolute top-0 left-0 flex h-9 cursor-pointer items-center justify-center rounded-full bg-black bg-opacity-40 opacity-0 duration-300 ease-in-out group-hover:opacity-100 !size-14"
                >
                  <CameraIcon class="size-4 cursor-pointer text-white" />
                </div>
              </component>
              <div
                v-if="uploading"
                class="w-full h-full top-0 left-0 absolute bg-black bg-opacity-20 rounded-full flex items-center justify-center"
              >
                <LoadingIndicator class="size-4" />
              </div>
            </div>
            <div class="flex flex-col gap-1">
              <div class="flex flex-col">
                <span
                  class="text-lg sm:text-xl !font-semibold text-ink-gray-8"
                  >{{ auth?.userName }}</span
                >
                <span class="text-p-sm text-ink-gray-6">{{ auth?.user }}</span>
              </div>
              <ErrorMessage :message="__(_error)" />
            </div>
          </div>
        </template>
      </FileUploader>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex items-center justify-between">
        <div class="flex gap-2 items-center">
          <div class="text-base font-semibold text-ink-gray-9">
            {{ __("Account info & security") }}
          </div>
          <Badge
            v-if="isAccountInfoDirty"
            :variant="'subtle'"
            :theme="'orange'"
            size="sm"
            :label="__('Unsaved changes')"
          />
        </div>
        <Button
          :label="__('Save')"
          @click="setAgent.submit()"
          :loading="setAgent.loading"
          :disabled="!isAccountInfoDirty"
        />
      </div>
      <div class="flex flex-col sm:flex-row items-center gap-2 mt-6">
        <FormControl
          class="w-full"
          :label="__('First Name')"
          maxlength="40"
          v-model="profile.firstName"
        />
        <FormControl
          class="w-full"
          :label="__('Last Name')"
          maxlength="40"
          v-model="profile.lastName"
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
    <ChangePasswordModal
      v-if="showChangePasswordModal"
      v-model="showChangePasswordModal"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import {
  Avatar,
  Badge,
  Button,
  createResource,
  Dropdown,
  FileUploader,
  LoadingIndicator,
  toast,
} from "frappe-ui";
import { __ } from "@/translation";
import { useAuthStore } from "@/stores/auth";
import CameraIcon from "~icons/lucide/camera";
import ChangePasswordModal from "./components/ChangePasswordModal.vue";
import { disableSettingModalOutsideClick } from "../settingsModal";

const auth = useAuthStore();
const profile = ref({
  fullName: auth.userName,
  userImage: auth.userImage,
  firstName: auth.userFirstName,
  lastName: auth.userLastName,
});
const showChangePasswordModal = ref(false);

const isAccountInfoDirty = computed(() => {
  const agentName = agentData.data?.agent_name?.split(" ");
  if (!agentName) return false;
  const isDirty =
    profile.value.firstName !== agentName[0] ||
    profile.value.lastName !== agentName[1];
  if (isDirty) {
    disableSettingModalOutsideClick.value = true;
  } else {
    disableSettingModalOutsideClick.value = false;
  }
  return isDirty;
});

const agentData = createResource({
  url: "helpdesk.helpdesk.doctype.hd_agent.hd_agent.get_agent",
  auto: true,
  onSuccess: (data) => {
    const fullName = data.agent_name.split(" ");
    profile.value = {
      fullName: data.agent_name,
      firstName: fullName[0],
      lastName: fullName[1] || "",
      userImage: data.user_image,
    };
  },
});

const setAgent = createResource({
  url: "frappe.client.set_value",
  validate: () => {
    if (!profile.value.firstName.trim()) {
      return __("Please enter first name at least");
    }
  },
  makeParams() {
    return {
      doctype: "HD Agent",
      name: agentData.data?.name,
      fieldname: {
        agent_name: `${profile.value.firstName} ${profile.value.lastName}`,
        user_image: profile.value.userImage,
      },
    };
  },
  onSuccess: () => {
    auth.reloadUser();
    agentData.reload();
    toast.success(__("Profile updated"));
  },
});

const updateImage = (file: string | null) => {
  profile.value.userImage = file;
  setAgent.submit();
};
</script>
