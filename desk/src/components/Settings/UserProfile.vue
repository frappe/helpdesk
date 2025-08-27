<template>
  <div class="flex h-full flex-col gap-6 p-8 text-ink-gray-8">
    <SettingsLayoutHeader title="User Profile" />
    <div class="flex-1 flex flex-col gap-6 mt-2 overflow-y-auto">
      <div v-if="profile" class="flex w-full items-center justify-between">
        <FileUploader
          @success="(file) => updateImage(file.file_url)"
          fileTypes="['image/*']"
        >
          <template #default="{ openFileSelector, error: _error }">
            <div class="flex items-center gap-4">
              <div class="group relative !size-[66px]">
                <Avatar
                  class="!size-16"
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
                              onClick: () => updateImage(),
                            },
                          ],
                        }
                      : { onClick: openFileSelector }
                  "
                  class="!absolute bottom-0 left-0 right-0"
                >
                  <div
                    class="z-1 absolute bottom-0.5 left-0 right-0.5 flex h-9 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-3 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
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
                <span class="text-2xl font-semibold text-ink-gray-8">
                  {{ profile.full_name }}
                </span>
                <span class="text-base text-ink-gray-7">
                  {{ profile.email }}
                </span>
                <ErrorMessage :message="__(_error)" />
              </div>
            </div>
          </template>
        </FileUploader>
        <Button
          :label="'Change Password'"
          icon-left="lock"
          @click="showChangePasswordModal = true"
        />
        <ChangePasswordModal
          v-if="showChangePasswordModal"
          v-model="showChangePasswordModal"
        />
      </div>
      <div class="flex flex-col gap-4">
        <div class="flex justify-between gap-4">
          <FormControl
            class="w-full"
            label="First Name"
            v-model="profile.first_name"
          />
          <FormControl
            class="w-full"
            label="Last Name"
            v-model="profile.last_name"
          />
        </div>
      </div>
    </div>
    <div class="flex justify-between items-center">
      <div>
        <ErrorMessage :message="error" />
      </div>
      <Button
        variant="solid"
        :label="__('Update')"
        :disabled="!dirty"
        :loading="updateAgent.loading || updateUser.loading"
        @click="updateProfile()"
      />
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from "@/stores/auth";

import { computed, onMounted, ref, watch } from "vue";
import {
  call,
  Dropdown,
  createResource,
  toast,
  FormControl,
  FileUploader,
  Avatar,
} from "frappe-ui";
import SettingsLayoutHeader from "./SettingsLayoutHeader.vue";
import ChangePasswordModal from "@/components/ChangePasswordModal.vue";
import CameraIcon from "@/components/icons/CameraIcon.vue";
const authStore = useAuthStore();
const profile = ref({});
const error = ref("");
const showChangePasswordModal = ref(false);
const initialProfile = ref({});

const userResource = createResource({
  url: "frappe.client.get_value",
  makeParams() {
    return {
      doctype: "HD Agent",
      fieldname: ["user_image", "agent_name", "user"],
      filters: { name: authStore.user },
    };
  },
  async onSuccess(data) {
    let agentData = data || {};
    if (!agentData.agent_name) {
      const userData = await call("frappe.client.get_value", {
        doctype: "User",
        fieldname: [
          "first_name",
          "last_name",
          "user_image",
          "full_name",
          "email",
        ],
        filters: { name: authStore.user },
      });
      profile.value = {
        ...userData,
      };
    } else {
      const [first, ...rest] = agentData.agent_name.split(" ");
      profile.value = {
        user_image: agentData.user_image || "",
        first_name: first || "",
        last_name: rest.join(" ") || "",
        full_name: agentData.agent_name || "",
        email: agentData.user || "",
      };
    }
    error.value = "";
  },
});

const dirty = computed(() => {
  return (
    profile.value.first_name !== initialProfile.value.first_name ||
    profile.value.last_name !== initialProfile.value.last_name ||
    profile.value.user_image !== initialProfile.value.user_image
  );
});

const updateAgent = createResource({
  url: "frappe.client.set_value",
  makeParams() {
    return {
      doctype: "HD Agent",
      name: authStore.user,
      fieldname: {
        agent_name: `${profile.value.first_name || ""} ${
          profile.value.last_name || ""
        }`.trim(),
        user_image: profile.value.user_image,
      },
    };
  },
  onSuccess(data) {
    updateUser.submit().then(() => {
      error.value = "";
      toast.success("Profile updated successfully");
      authStore.reloadUser();
    });
  },
  onError(err) {
    error.value = err.message || "Failed to update profile";
  },
});

const updateUser = createResource({
  url: "frappe.client.set_value",
  makeParams() {
    return {
      doctype: "User",
      name: authStore.user,
      fieldname: {
        first_name: profile.value.first_name,
        last_name: profile.value.last_name,
        user_image: profile.value.user_image,
      },
    };
  },
});

function updateImage(fileUrl = "") {
  profile.value.user_image = fileUrl;
}

async function updateProfile() {
  try {
    const agentExists = await checkAgentExists();
    if (agentExists) {
      updateAgent.submit();
    } else {
      updateUser.submit().then(() => {
        error.value = "";
        toast.success("Profile updated successfully");
        authStore.reloadUser();
      });
    }
  } catch (err) {
    error.value = err.message || "Failed to update profile";
  }
}

async function checkAgentExists() {
  try {
    const res = await call("frappe.client.get_value", {
      doctype: "HD Agent",
      fieldname: "name",
      filters: { name: authStore.user },
    });
    return res && res.name ? true : false;
  } catch (err) {
    console.log("Error checking agent existence:", err);
    return false;
  }
}

watch(
  () => [profile.value.first_name, profile.value.last_name],
  ([newFirst, newLast]) => {
    profile.value.full_name = `${newFirst || ""} ${newLast || ""}`.trim();
  }
);

onMounted(async () => {
  try {
    await userResource.submit();
    initialProfile.value = { ...profile.value };
  } catch (err) {
    error.value = err.message || "Failed to load profile";
  }
});
</script>

<style scoped></style>
