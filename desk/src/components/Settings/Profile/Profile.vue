<template>
  <SettingsLayoutBase
    :title="__('Profile')"
    :description="__('Manage your profile information.')"
  >
    <template #content>
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
                  <span class="text-p-sm text-ink-gray-6">{{
                    auth?.user
                  }}</span>
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
              {{ __("Account & Security") }}
            </div>
            <Badge
              v-if="isProfileDirty"
              :variant="'subtle'"
              :theme="'orange'"
              size="sm"
              :label="__('Unsaved')"
            />
          </div>
          <Button
            :label="__('Save')"
            variant="solid"
            class="transition-colors"
            @click="onSave"
            :loading="isProfileLoading"
            :disabled="!isProfileDirty"
          />
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5 mt-6">
          <FormControl
            class="w-full"
            :label="__('First name')"
            maxlength="40"
            v-model="profile.firstName"
          />
          <FormControl
            class="w-full"
            :label="__('Last name')"
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
        <div class="flex items-center justify-between mt-6">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __("Language") }}
            </span>
            <span class="text-p-sm text-ink-gray-6">{{
              __("Change language of the application.")
            }}</span>
          </div>
          <Link
            :model-value="language"
            @update:modelValue="language = $event || auth.language"
            doctype="Language"
            class="w-40"
          />
        </div>
        <div class="flex items-center justify-between mt-6">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __("Timezone") }}
            </span>
            <span class="text-p-sm text-ink-gray-6">{{
              __("Change timezone of the application.")
            }}</span>
          </div>
          <Autocomplete
            :options="timezoneOptions"
            :model-value="timezone"
            @update:modelValue="timezone = $event?.value"
            placeholder="Select Timezone"
            class="w-40"
          />
        </div>

        <div class="flex flex-col gap-2 mt-6">
          <div class="flex items-center justify-between">
            <div class="flex flex-col gap-1">
              <span class="text-base font-medium text-ink-gray-8">{{
                __("Email Signature")
              }}</span>
              <span class="text-p-sm text-ink-gray-6">{{
                __(
                  "Set a personalized email signature that appears at the end of your replies."
                )
              }}</span>
            </div>
            <Switch v-model="enableSignature" />
          </div>
          <div v-if="enableSignature">
            <TextEditor
              ref="signatureEditorRef"
              editor-class="prose-sm max-w-none min-h-[4rem]"
              :starterkit-options="{ heading: { levels: [2, 3, 4] } }"
              :placeholder="__('Write your email signature here')"
              :content="signatureContent"
              @change="(val) => (signatureContent = val)"
            >
              <template #editor="{ editor }">
                <EditorContent
                  class="max-h-[30vh] overflow-y-auto rounded-lg border p-4"
                  :editor="editor"
                />
              </template>
              <template #bottom>
                <div
                  class="mt-2 flex flex-col justify-between sm:flex-row sm:items-center"
                >
                  <TextEditorFixedMenu
                    class="-ml-1 overflow-x-auto"
                    :buttons="signatureButtons"
                  />
                  <Button
                    type="button"
                    size="sm"
                    variant="subtle"
                    class="w-fit"
                    :disabled="!isSignatureDirty"
                    @click="resetSignatureContent"
                    :tooltip="
                      isSignatureDirty &&
                      __('This will reset the content to the default message.')
                    "
                  >
                    {{ __("Reset Content") }}
                  </Button>
                </div>
              </template>
            </TextEditor>
          </div>
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
import { computed, ref, watch } from "vue";
import {
  Avatar,
  Badge,
  Button,
  createResource,
  Dropdown,
  FileUploader,
  LoadingIndicator,
  toast,
  TextEditor,
  TextEditorFixedMenu,
  Switch,
} from "frappe-ui";
import { EditorContent } from "@tiptap/vue-3";
import { Autocomplete } from "@/components";
import { __ } from "@/translation";
import { useAuthStore } from "@/stores/auth";
import {
  updateRes as updateSignature,
  updateRes as updateTimezone,
  updateRes as updateLanguage,
} from "@/stores/knowledgeBase";

import CameraIcon from "~icons/lucide/camera";
import ChangePasswordModal from "./components/ChangePasswordModal.vue";
import { disableSettingModalOutsideClick } from "../settingsModal";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import Link from "@/components/frappe-ui/Link.vue";
import { HDAgent } from "@/types/doctypes";

const auth = useAuthStore();
const profile = ref({
  fullName: auth.userName,
  userImage: auth.userImage,
  firstName: auth.userFirstName,
  lastName: auth.userLastName,
});
const showChangePasswordModal = ref(false);
const language = ref(auth.language);
const timezone = ref(auth.timezone);
const timezoneOptions = ref([]);

// Signature state
const signatureEditorRef = ref(null);
const enableSignature = ref(false);
const signatureContent = ref("");
const originalSignature = ref("");
const originalEnableSignature = ref(false);

const isSignatureDirty = computed(() => {
  return (
    signatureContent.value !== originalSignature.value ||
    enableSignature.value !== originalEnableSignature.value
  );
});

function resetSignatureContent() {
  signatureContent.value = originalSignature.value;
  enableSignature.value = originalEnableSignature.value;
}

const isLanguageChanged = computed(() => {
  return language.value !== auth?.language;
});

const isTimezoneChanged = computed(() => {
  return timezone.value !== auth?.timezone;
});

const isAccountInfoDirty = computed(() => {
  const agentName = agentData.data?.agent_name?.split(" ");
  if (!agentName) return false;
  return (
    profile.value.firstName !== agentName[0] ||
    profile.value.lastName !== (agentName[1] || "")
  );
});

const isProfileLoading = computed(() => {
  return (
    setAgent.loading ||
    updateLanguage.loading ||
    updateTimezone.loading ||
    updateSignature.loading
  );
});

const isProfileDirty = computed(
  () =>
    isAccountInfoDirty.value ||
    isLanguageChanged.value ||
    isTimezoneChanged.value ||
    isSignatureDirty.value
);
const signatureButtons = [
  "Paragraph",
  ["Heading 2", "Heading 3", "Heading 4"],
  "Separator",
  "Bold",
  "Italic",
  "Separator",
  "Bullet List",
  "Numbered List",
  "Separator",
  "Link",
  "Image",
];

const agentData = createResource({
  url: "frappe.client.get",
  auto: true,
  makeParams() {
    return {
      doctype: "HD Agent",
      name: auth.userId,
    };
  },
  onSuccess: (data: HDAgent) => {
    const fullName = data.agent_name.split(" ");
    profile.value = {
      fullName: data.agent_name,
      firstName: fullName[0],
      lastName: fullName[1] || "",
      userImage: data.user_image,
    };
  },
});

// Fetch the user's email_signature from the User doctype
const userData = createResource({
  url: "frappe.client.get",
  auto: true,
  makeParams() {
    return {
      doctype: "User",
      name: auth.userId,
      fields: ["email_signature"],
    };
  },
  onSuccess: (data: { email_signature?: string }) => {
    const sig = data.email_signature || "";
    signatureContent.value = sig;
    originalSignature.value = sig;
    enableSignature.value = !!sig;
    originalEnableSignature.value = !!sig;
  },
});

const timezoneData = createResource({
  url: "frappe.core.doctype.user.user.get_timezones",
  auto: true,
  onSuccess(data) {
    timezoneOptions.value = data.timezones.map((tz: any) => ({
      label: tz,
      value: tz,
    }));
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
    toast.success(__("Profile updated successfully."));
  },
});

function handleLanguageChange() {
  updateLanguage.submit(
    {
      doctype: "User",
      name: auth.userId,
      fieldname: {
        language: language.value,
      },
    },
    {
      onSuccess() {
        toast.success(__("Language updated successfully."));
        setTimeout(() => {
          window.location.reload(true);
        }, 500);
      },
    }
  );
}

function handleTimezoneChange() {
  updateTimezone.submit(
    {
      doctype: "User",
      name: auth.userId,
      fieldname: {
        time_zone: timezone.value,
      },
    },
    {
      onSuccess() {
        toast.success(__("Timezone updated successfully."));
        setTimeout(() => {
          window.location.reload(true);
        }, 500);
      },
    }
  );
}

function handleSignatureUpdate() {
  updateSignature.submit(
    {
      doctype: "User",
      name: auth.userId,
      fieldname: {
        email_signature: enableSignature.value ? signatureContent.value : "",
      },
    },
    {
      onSuccess() {
        originalSignature.value = enableSignature.value
          ? signatureContent.value
          : "";
        originalEnableSignature.value = enableSignature.value;
        toast.success(__("Email signature updated successfully."));
      },
    }
  );
}

const onSave = () => {
  if (isAccountInfoDirty.value) {
    setAgent.submit();
  }

  if (isLanguageChanged.value) {
    handleLanguageChange();
  }

  if (isTimezoneChanged.value) {
    handleTimezoneChange();
  }

  if (isSignatureDirty.value) {
    handleSignatureUpdate();
  }
};

watch(isProfileDirty, (val) => {
  disableSettingModalOutsideClick.value = val;
});

const updateImage = (file: string | null) => {
  profile.value.userImage = file;
  setAgent.submit();
};
</script>
