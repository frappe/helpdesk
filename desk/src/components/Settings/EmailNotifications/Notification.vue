<template>
  <form
    @submit.prevent="props.onSubmit"
    class="flex-grow flex flex-col isolate"
  >
    <!-- Header -->
    <div class="sticky top-0 z-10 bg-white py-8">
      <SettingsLayoutHeader :description="props.description">
        <template #title>
          <div class="flex items-center gap-x-1">
            <div class="pl-6 pr-2 relative">
              <button
                @click="props.onBack"
                class="absolute top-0 -left-1 w-full h-full text-ink-gray-7 hover:text-black peer"
              >
                <span class="sr-only">{{
                  __("back to email event list")
                }}</span>
                <LucideChevronLeft class="w-5 h-5" />
              </button>
              <h1
                class="font-semibold text-ink-gray-7 text-xl peer-hover:text-black"
              >
                {{ props.title }}
              </h1>
            </div>
            <Badge
              v-if="unsavedChanges"
              :variant="'subtle'"
              :theme="'red'"
              size="sm"
              :label="__('Not Saved')"
            />
          </div>
        </template>
        <template #actions>
          <div
            :inert="notificationDataResource.loading"
            class="flex items-center gap-x-2"
            :class="{ invisible: notificationDataResource.loading }"
          >
            <Switch
              size="sm"
              :label="__('Enabled')"
              v-model="enabled"
              @update:model-value="setUnsavedChanges"
              :style="{ background: 'transparent' }"
              class="flex-row-reverse gap-x-2 text-sm text-ink-gray-7 font-medium pl-0"
            />
            <Button
              type="submit"
              :label="__('Save')"
              theme="gray"
              variant="solid"
              :disabled="!unsavedChanges"
              :loading="props.submitting"
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
        <div class="flex flex-col gap-1">
          <FormControl
            type="textarea"
            size="sm"
            :label="__('Email Content')"
            :required="true"
            :rows="10"
            v-model="content"
            :oninput="setUnsavedChanges"
          />
          <p class="text-sm text-gray-700 leading-5">
            {{
              __(
                "Find out all of the identifiers that can be used in the content"
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
            type="button"
            size="sm"
            variant="subtle"
            @click="resetContent"
            class="w-fit"
          >
            {{ __("Reset Content") }}
          </Button>
        </div>
      </template>
      <LoadingIndicator v-else class="w-4" />
    </div>
  </form>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { NotificationName } from "./types";
import { createResource, Switch, LoadingIndicator } from "frappe-ui";
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";

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
  if (content.value !== props.defaultContent) {
    content.value = props.defaultContent;
    setUnsavedChanges();
  }
}

defineExpose({
  setUnsavedChanges,
  resetUnsavedChanges,
});
</script>

<style scoped></style>
