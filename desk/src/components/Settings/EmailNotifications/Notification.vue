<template>
  <div class="flex-grow flex flex-col isolate">
    <!-- Header -->
    <div class="sticky top-0 z-10 bg-white py-8">
      <SettingsLayoutHeader :description="props.description">
        <template #title>
          <div class="flex items-center">
            <div
              class="pl-5 pr-2 relative text-ink-gray-7 hover:opacity-70 min-h-8 flex items-center"
            >
              <button
                type="button"
                @click="internalOnBack"
                class="absolute top-0 -left-[0.375rem] w-full h-full"
              >
                <span class="sr-only">{{
                  __("back to email event list")
                }}</span>
                <LucideChevronLeft class="w-4.5 h-4.5" />
              </button>
              <h1 class="font-semibold text-xl">
                {{ props.title }}
              </h1>
            </div>
            <Badge
              v-if="unsavedChanges"
              :variant="'subtle'"
              :theme="'orange'"
              size="sm"
              :label="__('Unsaved')"
            />
          </div>
        </template>
        <template #actions>
          <div
            :inert="notificationDataResource.loading"
            class="flex items-center gap-x-4 pt-[0.125rem]"
            :class="{ invisible: notificationDataResource.loading }"
          >
            <Switch
              size="sm"
              :label="__('Enabled')"
              v-model="enabled"
              @update:model-value="setUnsavedChanges"
              :style="{ background: 'transparent', padding: '0px' }"
              class="flex-row-reverse gap-x-2 pl-0"
            />
            <Button
              type="button"
              :label="__('Save')"
              theme="gray"
              variant="solid"
              :disabled="!unsavedChanges"
              :loading="props.submitting"
              @click="props.onSubmit"
            />
          </div>
        </template>
      </SettingsLayoutHeader>
    </div>
    <!-- Body -->
    <div
      class="flex flex-col gap-8 flex-grow pb-8"
      :class="{
        'items-center justify-center': notificationDataResource.loading,
      }"
    >
      <template v-if="!notificationDataResource.loading">
        <slot name="formFields"></slot>
        <div class="flex flex-col gap-2">
          <FormControl
            type="textarea"
            size="sm"
            :label="__('Email Content')"
            :required="true"
            :rows="10"
            v-model="content"
            :oninput="setUnsavedChanges"
          />
          <div class="flex gap-x-1 items-start justify-between">
            <p class="text-sm text-gray-700 leading-5">
              {{
                __(
                  "Find out all of the variables that can be used in the content"
                )
              }}
              <a
                :href="props.documentationLink"
                target="_blank"
                class="underline font-semibold"
                >{{ __("here") }}</a
              >
            </p>
            <Button
              :disabled="content === defaultContent"
              type="button"
              size="sm"
              variant="subtle"
              @click="onResetContent"
              class="w-fit"
            >
              {{ __("Reset Content") }}
            </Button>
          </div>
        </div>
      </template>
      <LoadingIndicator v-else class="w-4" />
    </div>
  </div>
  <ConfirmDialog
    v-model="showUnsavedConfirm"
    :title="__('Unsaved changes')"
    :message="
      __('Are you sure you want to go back? Unsaved changes will be lost.')
    "
    :onConfirm="
      () => {
        disableSettingModalOutsideClick = false;
        props.onBack();
      }
    "
  />
  <ConfirmDialog
    v-model="showContentChangeConfirm"
    :title="__('Reset content')"
    :message="
      __(
        'Are you sure you want to reset the content? Current content will be overridden.'
      )
    "
    :onConfirm="
      () => {
        resetContent();
        showContentChangeConfirm = false;
      }
    "
  />
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import type { NotificationName } from "./types";
import { createResource, Switch, LoadingIndicator } from "frappe-ui";
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import { disableSettingModalOutsideClick } from "../settingsModal";

const props = defineProps<{
  title: string;
  description: string;
  documentationLink: string;
  defaultContent: string;
  onBack: () => void;
  onSubmit: (e: Event & { target: HTMLFormElement }) => void;
  onGetDataSuccess: (data: any) => void;
  submitting: boolean;
  name: NotificationName;
}>();

const content = defineModel<string>("content", { required: true });
const enabled = defineModel<boolean>("enabled", { required: true });

const unsavedChanges = ref(false);
const showUnsavedConfirm = ref(false);
const showContentChangeConfirm = ref(false);

const notificationDataResource = createResource({
  url: "helpdesk.api.settings.email_notifications.get_data",
  method: "GET",
  params: {
    notification: props.name,
  },
  auto: true,
  onSuccess: props.onGetDataSuccess,
});

function setUnsavedChanges() {
  unsavedChanges.value = true;
}

function resetUnsavedChanges() {
  unsavedChanges.value = false;
}

function resetContent() {
  content.value = props.defaultContent;
  setUnsavedChanges();
}

function onResetContent() {
  if (content.value !== props.defaultContent) {
    showContentChangeConfirm.value = true;
  }
}

function internalOnBack() {
  if (unsavedChanges.value) {
    showUnsavedConfirm.value = true;
    return;
  }
  disableSettingModalOutsideClick.value = false;
  props.onBack();
}

watch(
  () => unsavedChanges.value,
  (val) => {
    disableSettingModalOutsideClick.value = val;
  }
);

defineExpose({
  setUnsavedChanges,
  resetUnsavedChanges,
});
</script>
