<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="__('Email Settings')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-xl hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="goBack"
        />
        <Transition name="fade">
          <Badge
            v-if="isDirty"
            :label="__('Not Saved')"
            variant="subtle"
            theme="orange"
        /></Transition>
      </div>
    </template>
    <template #header-actions>
      <Transition name="fade">
        <div v-if="isDirty">
          <Button
            variant="solid"
            :label="__('Update')"
            :loading="user?.save?.loading"
            @click="update"
          /></div
      ></Transition>
    </template>
    <template #content>
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">
            {{ __("Signature") }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{ __("Manage your email signature.") }}
          </span>
        </div>
        <TextEditor
          editor-class="!prose-sm max-w-full overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded-b border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors -mt-0.5"
          :content="user?.doc?.email_signature"
          :placeholder="__('Write your email signature here.')"
          :bubbleMenu="true"
          :fixed-menu="true"
          @change="(val) => (user.doc.email_signature = val)"
        />
      </div>
      <div class="flex flex-col gap-4 mt-6">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">
            {{ __("Emails") }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                "Switch between outgoing email accounts when sending emails from your configured accounts."
              )
            }}
          </span>
        </div>
        <div>
          <div
            v-if="user.doc.user_emails?.length"
            class="w-full border rounded-md mb-2 border-outline-gray-modals"
          >
            <div
              class="grid grid-cols-[4fr_4fr_0.3fr] gap-2 px-4 py-3 text-sm font-medium text-ink-gray-5 border-b border-outline-gray-modals"
            >
              <span>{{ __("Email Account") }}</span>
              <span>{{ __("Email") }}</span>
              <span></span>
            </div>
            <div
              v-for="e in user.doc.user_emails"
              :key="e.name"
              class="grid grid-cols-[4fr_4fr_0.3fr] gap-2 group items-center px-4 py-2.5 text-base border-b border-outline-gray-modals last:border-b-0"
            >
              <span class="text-ink-gray-8 font-medium truncate">
                {{ e.email_account }}
              </span>
              <span class="text-ink-gray-6 truncate">{{ e.email_id }}</span>
              <div class="group-hover:opacity-100 opacity-0 transition-opacity">
                <Button
                  class="w-10"
                  variant="ghost"
                  :tooltip="__('Remove')"
                  icon="x"
                  @click.prevent="removeEmail(e)"
                />
              </div>
            </div>
          </div>
          <Autocomplete
            value=""
            :options="filteredEmails"
            @change="(e) => addEmail(e)"
          >
            <template #target="{ togglePopover }">
              <Button
                class="!bg-surface-modal"
                variant="outline"
                :label="__('Add Email')"
                iconLeft="plus"
                @click="togglePopover()"
              />
            </template>
            <template #item-label="{ option }">
              <div class="flex flex-col gap-1 text-ink-gray-9">
                <div>{{ option.label }}</div>
                <div class="text-ink-gray-4 text-sm">
                  {{ option.email }}
                </div>
              </div>
            </template>
          </Autocomplete>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <ConfirmDialog
    v-model="showConfirmDialog.show"
    :title="showConfirmDialog.title"
    :message="showConfirmDialog.message"
    :onConfirm="showConfirmDialog.onConfirm"
    :onCancel="
      () => {
        if (showConfirmDialog.onCancel) {
          showConfirmDialog.onCancel();
        } else {
          showConfirmDialog.show = false;
        }
      }
    "
  />
</template>
<script setup>
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import Autocomplete from "@/components/frappe-ui/Autocomplete.vue";
import {
  Badge,
  Button,
  createDocumentResource,
  createResource,
  TextEditor,
  toast,
} from "frappe-ui";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { computed, ref, watch } from "vue";
import { useAuthStore } from "@/stores/auth";
import { disableSettingModalOutsideClick } from "../settingsModal";
const { userId } = useAuthStore();
const user = createDocumentResource({ doctype: "User", name: userId });
const emit = defineEmits(["updateStep"]);
import { __ } from "@/translation";
import { normalize } from "@/utils";

const currentUserEmailInfo = createResource({
  url: "helpdesk.api.auth.get_current_user_email_info",
  cache: "current-user-email-info",
  auto: true,
});

const filteredEmails = computed(() => {
  if (!currentUserEmailInfo.data?.available_emails) return [];
  const linkedEmails = user.doc.user_emails?.map((e) => e.email_id) || [];
  return currentUserEmailInfo.data.available_emails
    .map((doc) => ({
      label: doc.name,
      value: doc.name,
      email: doc.email_id,
    }))
    .filter((e) => !linkedEmails.includes(e.email));
});

const isSignatureDirty = computed(() => {
  return (
    normalize(currentUserEmailInfo.data?.email_signature) !==
    normalize(user?.doc?.email_signature)
  );
});

const isUserEmailListDirty = computed(() => {
  const emailIds = (list = []) => list.map((e) => e.email_id).sort();
  return (
    JSON.stringify(emailIds(currentUserEmailInfo.data?.outgoing_emails)) !==
    JSON.stringify(emailIds(user.doc.user_emails))
  );
});

const isDirty = computed(() => {
  return isSignatureDirty.value || isUserEmailListDirty.value;
});

if (isDirty.value) {
  disableSettingModalOutsideClick.value = true;
} else {
  disableSettingModalOutsideClick.value = false;
}

function addEmail(email) {
  if (!user.doc.user_emails) user.doc.user_emails = [];
  user.doc.user_emails.push({
    email_account: email.label,
    email_id: email.email,
  });
}

function removeEmail(email) {
  user.doc.user_emails = user.doc.user_emails.filter(
    (e) => e.email_id !== email.email_id
  );
}

function update() {
  user.save.submit(null, {
    onSuccess: () => {
      toast.success(__("Email settings updated successfully."));
      currentUserEmailInfo.reload();
      user.reload();
    },
  });
}

watch(isDirty, (val) => {
  disableSettingModalOutsideClick.value = val;
});

const showConfirmDialog = ref({
  show: false,
  title: "",
  message: "",
  onConfirm: () => {},
});

const goBack = () => {
  const confirmDialogInfo = {
    show: true,
    title: __("Unsaved changes"),
    message: __(
      "Are you sure you want to go back? Unsaved changes will be lost."
    ),
    onConfirm: goBack,
  };
  if (isDirty.value && !showConfirmDialog.value.show) {
    showConfirmDialog.value = confirmDialogInfo;
    return;
  }

  showConfirmDialog.value.show = false;
  emit("updateStep", "profile");
};
</script>
