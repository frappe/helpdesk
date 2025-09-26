<template>
  <SettingsHeader :routes="routes" />
  <div class="max-w-3xl xl:max-w-4xl mx-auto w-full p-4 lg:py-8">
    <div class="flex items-center justify-between gap-2">
      <FileUploader
        :fileTypes="['image/*']"
        @success="
          (file) => {
            updateImage(file.file_url);
          }
        "
      >
        <template #default="{ openFileSelector, error: _error }">
          <div class="flex items-center justify-center gap-2">
            <div class="group relative !size-14">
              <Avatar
                class="!size-14"
                :image="profile.user_image"
                :label="profile.full_name"
              />
              <component
                :is="profile.user_image ? Dropdown : 'div'"
                v-bind="
                  profile.user_image
                    ? {
                        options: [
                          {
                            icon: 'upload',
                            label: profile.user_image
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
                class="!absolute bottom-0 left-0 right-0"
              >
                <div
                  class="z-1 absolute bottom-0 left-0 right-0 flex h-9 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-3 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                  style="
                    -webkit-clip-path: inset(12px 0 0 0);
                    clip-path: inset(12px 0 0 0);
                  "
                >
                  <CameraIcon class="size-4 cursor-pointer text-white" />
                </div>
              </component>
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
      <Button
        icon-left="lock"
        label="Change Password"
        @click="showChangePasswordModal = true"
      />
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex items-center justify-between">
        <div class="text-lg font-semibold text-ink-gray-9">Account info</div>
        <Button
          label="Save"
          @click="setUser.submit()"
          :loading="setUser.loading"
          :disabled="!isAccountInfoDirty"
        />
      </div>
      <div class="flex flex-col sm:flex-row items-center gap-2 mt-6">
        <FormControl
          class="w-full"
          label="First Name"
          v-model="profile.user_first_name"
        />
        <FormControl
          class="w-full"
          label="Last Name"
          v-model="profile.user_last_name"
        />
      </div>
    </div>
  </div>
  <ChangePasswordModal
    v-if="showChangePasswordModal"
    v-model="showChangePasswordModal"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import SettingsHeader from "../components/SettingsHeader.vue";
import {
  Avatar,
  Button,
  createResource,
  Dropdown,
  FileUploader,
  toast,
} from "frappe-ui";
import { __ } from "@/translation";
import ChangePasswordModal from "./components/ChangePasswordModal.vue";
import { useAuthStore } from "@/stores/auth";
import CameraIcon from "~icons/lucide/camera";

const auth = useAuthStore();
const profile = ref({
  full_name: auth.userName,
  user_image: auth.userImage,
  user_first_name: auth.userFirstName,
  user_last_name: auth.userLastName,
  email: auth.userId,
});
const showChangePasswordModal = ref(false);

const isAccountInfoDirty = computed(() => {
  return (
    profile.value.user_first_name !== auth.userFirstName ||
    profile.value.user_last_name !== auth.userLastName
  );
});

const routes = computed(() => [
  {
    label: "Profile",
    route: "/settings/profile",
  },
]);

const setUser = createResource({
  url: "frappe.client.set_value",
  makeParams() {
    return {
      doctype: "User",
      name: auth.user,
      fieldname: {
        user_image: profile.value.user_image,
        first_name: profile.value.user_first_name,
        last_name: profile.value.user_last_name,
      },
    };
  },
  onSuccess: () => {
    auth.reloadUser();
    toast.success(__("Profile updated"));
  },
});

const updateImage = (file: string | null) => {
  profile.value.user_image = file;
  setUser.submit();
};

onMounted(() => {
  profile.value = {
    full_name: auth.userName,
    user_image: auth.userImage,
    user_first_name: auth.userFirstName,
    user_last_name: auth.userLastName,
    email: auth.userId,
  };
});
</script>
