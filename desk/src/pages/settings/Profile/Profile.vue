<template>
  <SettingsHeader :routes="routes" />
  <div class="max-w-3xl xl:max-w-4xl mx-auto w-full p-4 lg:py-8">
    <div class="flex items-center justify-between gap-2">
      <div class="flex items-center gap-2">
        <Avatar size="3xl" :image="auth?.userImage" :label="auth?.userName" />
        <div class="flex flex-col">
          <span class="text-lg sm:text-xl !font-semibold text-ink-gray-8">{{
            auth?.userName
          }}</span>
          <span class="text-p-sm text-ink-gray-6">{{ auth?.user }}</span>
        </div>
      </div>
      <div>
        <FileUploader
          v-if="!auth?.userImage"
          :fileTypes="['image/*']"
          @success="
            (file) => {
              updateImage(file.file_url);
            }
          "
        >
          <template #default="{ openFileSelector }">
            <Button
              @click="openFileSelector()"
              iconLeft="upload"
              label="Upload Image"
            />
          </template>
        </FileUploader>

        <div v-else>
          <Button label="Remove" iconLeft="trash" @click="updateImage(null)" />
        </div>
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="text-lg font-semibold text-ink-gray-9">
        Account info & security
      </div>
      <div class="flex items-center justify-between gap-2 mt-6">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">Email</span>
          <span class="text-p-sm text-ink-gray-6">{{ auth?.user }}</span>
        </div>
        <Button label="Change Email" @click="showChangeEmailModal = true" />
      </div>
      <div class="flex items-center justify-between gap-2 mt-6">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">Password</span>
          <span class="text-p-sm text-ink-gray-6"
            >Change your account password for security.</span
          >
        </div>
        <Button
          label="Change Password"
          @click="showChangePasswordModal = true"
        />
      </div>
    </div>
  </div>
  <ChangePasswordModal
    v-if="showChangePasswordModal"
    v-model="showChangePasswordModal"
  />
  <ChangeEmailModal
    v-if="showChangeEmailModal"
    v-model="showChangeEmailModal"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import SettingsHeader from "../components/SettingsHeader.vue";
import { Avatar, createResource, FileUploader, toast } from "frappe-ui";
import { __ } from "@/translation";
import ChangePasswordModal from "./components/ChangePasswordModal.vue";
import ChangeEmailModal from "./components/ChangeEmailModal.vue";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const profile = ref({
  user_image: auth.userImage,
});
const showChangePasswordModal = ref(false);
const showChangeEmailModal = ref(false);

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
  profile.value.user_image = auth.userImage;
});
</script>
