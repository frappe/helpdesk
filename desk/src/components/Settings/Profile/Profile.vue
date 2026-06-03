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
            <div class="flex items-center justify-center gap-4">
              <div class="group relative flex-shrink-0 size-16">
                <Avatar
                  class="!size-16"
                  :image="user.doc?.user_image"
                  :label="fullName"
                />
                <div
                  v-if="currentStatus"
                  class="absolute bottom-0.5 right-0.5 size-3.5 rounded-full outline outline-white outline-4"
                  :class="agentStatusStore.statusColor(currentStatus)"
                />
                <Tooltip
                  :hoverDelay="0"
                  placement="bottom"
                  :text="profileTooltipText"
                >
                  <div
                    class="z-1 absolute top-0 left-0 flex h-9 cursor-pointer items-center justify-center rounded-full !size-16"
                    @click.stop="openFileSelector"
                  />
                  <div
                    v-if="user.doc?.user_image"
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
                  class="w-full h-full top-0 left-0 absolute bg-surface-gray-7 bg-opacity-20 rounded-full flex items-center justify-center"
                >
                  <LoadingIndicator class="size-4" />
                </div>
              </div>
<<<<<<< HEAD
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
                      @keydown.enter="isNameDirty ? save() : (editName = false)"
                      @keydown.esc.stop="editName = false"
                    />
                    <Button
                      variant="outline"
                      icon="lucide-check"
                      :loading="user?.save?.loading"
                      :disabled="user?.save?.loading"
                      @click="isNameDirty ? save() : (editName = false)"
                    />
                  </div>
                  <span class="text-p-sm text-ink-gray-6">
                    {{ user?.doc?.email }}
=======
              <div class="flex flex-col gap-0.5 min-w-0">
                <div v-if="!editName" class="flex items-center gap-1">
                  <span class="text-lg font-semibold text-ink-gray-9 truncate">
                    {{ user?.doc?.full_name }}
>>>>>>> 630704fb (feat: add agent status indicators to frontend)
                  </span>
                  <Button
                    class="!px-1 !h-5 flex-shrink-0"
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
                    @keydown.enter="isNameDirty ? save() : (editName = false)"
                    @keydown.esc.stop="editName = false"
                  />
                  <Button
                    variant="outline"
                    icon="check"
                    :loading="user?.save?.loading"
                    :disabled="user?.save?.loading"
                    @click="isNameDirty ? save() : (editName = false)"
                  />
                </div>
                <span class="text-p-sm text-ink-gray-5 truncate">
                  {{ user?.doc?.email }}
                </span>
                <div class="flex items-center">
                  <AvailabilityMenu class="!min-h-0 !px-0" />
                  <IconDot class="size-4 text-ink-gray-5" />
                  <div
                    v-if="agentCreationDate?.data?.creation"
                    class="flex items-center gap-1 ml-[1px]"
                  >
                    <LucideCalendar class="size-4 text-ink-gray-5" />
                    <span class="text-ink-gray-7 text-p-sm"
                      >Joined
                      {{
                        dateFormat(
                          agentCreationDate.data.creation,
                          "MMM D, YYYY"
                        )
                      }}</span
                    >
                  </div>
                  <IconDot class="size-4 text-ink-gray-5" />

                  <div class="flex items-center gap-1 ml-[1px]">
                    <LucideGlobe class="size-4 text-ink-gray-5" />
                    <span class="text-p-sm text-ink-gray-7">{{
                      user?.doc?.time_zone
                    }}</span>
                  </div>
                </div>
                <ErrorMessage :message="__(_error)" />
              </div>
            </div>
          </template>
        </FileUploader>
      </div>
      <div>
        <div class="flex items-center justify-between h-7">
          <div class="flex gap-2 items-center">
            <span class="text-base font-semibold text-ink-gray-9">
              {{ __("Account Info & Security") }}
            </span>
            <UnsavedBadge :show="isDirty" />
          </div>

          <Transition name="fade">
            <Button
              variant="solid"
              v-if="isDirty"
              :label="__('Save')"
              :loading="user?.save?.loading"
              @click="save()"
          /></Transition>
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
          icon-left="lucide-lock"
          :label="__('Change Password')"
          @click="showChangePasswordModal = true"
        />
      </div>
      <div>
        <div class="flex items-center justify-between mt-6">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __("Language") }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __("Change language of the application.") }}
            </span>
          </div>
          <Link
            :model-value="user.doc?.language"
            @update:modelValue="updateLanguage"
            doctype="Language"
            class="w-40"
          />
        </div>
        <div class="flex items-center justify-between mt-6">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __("Timezone") }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __("Change timezone of the application.") }}
            </span>
          </div>
          <Autocomplete
            :model-value="user.doc?.time_zone"
            @update:modelValue="updateTimezone"
            class="w-40"
            :options="timezoneOptions"
            size="sm"
            placeholder="Select Timezone"
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
  Button,
  FileUploader,
  LoadingIndicator,
  toast,
  createDocumentResource,
  createResource,
} from "frappe-ui";
import LucideCalendar from "~icons/lucide/calendar";
import LucideGlobe from "~icons/lucide/globe";
import IconDot from "~icons/lucide/dot";

import { __ } from "@/translation";
import { useAuthStore } from "@/stores/auth";
import EditIcon from "~icons/lucide/edit";
const emit = defineEmits(["updateStep"]);

import AvailabilityMenu from "@/components/AvailabilityMenu.vue";
import { useAvailability } from "@/composables/useAvailability";
import { useAgentStatusStore } from "@/stores/agentStatus";
import ChangePasswordModal from "./components/ChangePasswordModal.vue";

const { currentStatus } = useAvailability();
const agentStatusStore = useAgentStatusStore();
import { disableSettingModalOutsideClick } from "../settingsModal";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import UnsavedBadge from "@/components/UnsavedBadge.vue";
import { dateFormat } from "@/utils";
const showChangePasswordModal = ref(false);

const { userId } = useAuthStore();
const user = createDocumentResource({ doctype: "User", name: userId });
const currentAgentName = (window as any).agent as string | null;
const agentCreationDate = currentAgentName
  ? createResource({
      url: "frappe.client.get_value",
      params: {
        doctype: "HD Agent",
        filters: currentAgentName,
        fieldname: "creation",
      },
      auto: true,
    })
  : null;

const isHoveringRemove = ref(false);
const editName = ref(false);

const profileTooltipText = computed(() => {
  if (isHoveringRemove.value) return __("Remove Photo");
  return user.doc?.user_image ? __("Change Photo") : __("Upload Photo");
});

const fullNameRef = useTemplateRef("fullNameRef");
const fullName = computed({
  get: () => user.doc?.full_name ?? "",
  set: (val) => {
    if (!user.doc) return;
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
  if (!user.originalDoc) return false;
  return user.doc?.time_zone !== user.originalDoc?.time_zone ||
    user.doc?.language !== user.originalDoc?.language
    ? true
    : false;
});

const isNameDirty = computed(() => {
  return (
    user.doc?.first_name !== user.originalDoc?.first_name ||
    user.doc?.last_name !== user.originalDoc?.last_name
  );
});

function save() {
  refreshRequired.value =
    user.doc?.language !== user.originalDoc?.language ||
    user.doc?.time_zone !== user.originalDoc?.time_zone;

  user.save.submit(null, {
    onSuccess: () => {
      editName.value = false;
      toast.success(__("Profile updated successfully."));
      if (refreshRequired.value) {
        window.location.reload();
      }
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

function updateLanguage(val: string | null) {
  if (!user.doc) return;
  user.doc.language = val || user.originalDoc?.language;
}

function updateTimezone(val: { label: string; value: string } | null) {
  if (!user.doc) return;
  user.doc.time_zone = val?.value || user.originalDoc?.time_zone;
}

const timezoneOptions = ref([]);
const timezoneData = createResource({
  url: "frappe.core.doctype.user.user.get_timezones",
  auto: true,
  onSuccess(data) {
    timezoneOptions.value = data.timezones.map((tz) => ({
      label: tz,
      value: tz,
    }));
  },
});

const language = ref(null);
const timezone = ref(null);

const refreshRequired = ref(false);

watch(
  () => user.doc,
  (doc) => {
    if (!doc) return;
    if (!language.value) language.value = doc.language;
    if (!timezone.value) timezone.value = doc.time_zone;
  },
  { immediate: true }
);

watch(isDirty, (val) => {
  disableSettingModalOutsideClick.value = val;
});
</script>
