<template>
  <SettingsHeader :routes="routes" />
  <div class="max-w-3xl xl:max-w-4xl mx-auto w-full p-4 lg:py-8">
    <SettingsLayoutHeader
      :description="__('Sent to the user right after creating an email ticket')"
    >
      <template #title>
        <div class="w-full items-center flex gap-2">
          <Button
            variant="ghost"
            icon-left="chevron-left"
            :label="__('Acknowledgement')"
            size="md"
            @click="goBack()"
            class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-xl font-semibold text-ink-gray-8 hover:opacity-70 !pr-0 max-w-[90%]"
          />
          <Badge
            :variant="'subtle'"
            :theme="'orange'"
            size="sm"
            :label="__('Unsaved')"
            v-if="isDirty"
          />
        </div>
      </template>
      <template #actions>
        <div class="flex items-center gap-4">
          <Switch
            size="sm"
            :label="__('Enabled')"
            v-model="notificationData.enabled"
            :style="{ background: 'transparent' }"
            class="!p-0"
          />
          <Button
            variant="solid"
            size="sm"
            :label="__('Save')"
            @click="onSave"
            :disabled="!isDirty"
          />
        </div>
      </template>
    </SettingsLayoutHeader>
    <div class="flex flex-col gap-2 mt-8">
      <FormControl
        type="textarea"
        size="sm"
        :label="__('Email Content')"
        :required="true"
        :rows="10"
        v-model="notificationData.content"
      />
    </div>
    <div class="flex gap-x-1 items-start justify-between mt-6">
      <p class="text-sm text-gray-700 leading-5">
        {{
          __("Find out all of the variables that can be used in the content")
        }}
        <a
          href="https://docs.frappe.io/helpdesk/email-notifications#available-variables-acknowledgement"
          target="_blank"
          class="underline font-semibold"
          >{{ __("here") }}</a
        >
      </p>
      <Button
        :disabled="isContentSame"
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

<script setup lang="ts">
import {
  Badge,
  Button,
  createResource,
  FormControl,
  Switch,
  toast,
} from "frappe-ui";
import { computed, ref } from "vue";
import SettingsHeader from "../components/SettingsHeader.vue";
import SettingsLayoutHeader from "@/pages/settings/components/SettingsLayoutHeader.vue";
import { onBeforeRouteLeave, useRouter } from "vue-router";
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";

const { $dialog } = globalStore();
const router = useRouter();
const routes = computed(() => [
  {
    label: "Email Notifications",
    route: "/settings/email-notifications",
  },
  {
    label: "Acknowledgement",
    route: "/settings/email-notifications/acknowledgement",
  },
]);

const notificationData = ref({
  enabled: false,
  content: "",
});

const isDirty = computed(() => {
  const data = {
    enabled: notificationDataResource.data?.enabled,
    content: notificationDataResource.data?.content,
  };
  return JSON.stringify(notificationData.value) !== JSON.stringify(data);
});

const isContentSame = computed(() => {
  return (
    notificationData.value.content ===
    notificationDataResource.data?.default_content
  );
});

const notificationDataResource = createResource({
  url: "helpdesk.api.settings.email_notifications.get_data",
  method: "GET",
  auto: true,
  params: {
    notification: "acknowledgement",
  },
  onSuccess: (data) => {
    notificationData.value = {
      enabled: data.enabled,
      content: data.content,
    };
  },
});

function goBack() {
  router.push({ name: "EmailNotificationsSettings" });
}

const updateSettings = createResource({
  url: "helpdesk.api.settings.email_notifications.update_acknowledgement",
  method: "PUT",
  auto: false,
  onSuccess() {
    toast.success("Settings updated");
    notificationDataResource.reload();
  },
});

const onSave = () => {
  updateSettings.submit({
    enabled: notificationData.value.enabled,
    content: notificationData.value.content,
  });
};

const onResetContent = () => {
  $dialog({
    title: __("Reset Content"),
    message: __(
      "Are you sure you want to reset the content? Current content will be overridden."
    ),
    actions: [
      {
        label: "Reset",
        variant: "solid",
        onClick: (close) => {
          notificationData.value.content =
            notificationDataResource.data?.default_content;
          close();
        },
      },
    ],
  });
};

const confirmLeave = () => {
  return new Promise<boolean>((resolve) => {
    $dialog({
      title: __("Unsaved changes"),
      message: __(
        "Are you sure you want to leave? Unsaved changes will be lost."
      ),
      actions: [
        {
          label: "Confirm",
          variant: "solid",
          onClick: (close: Function) => {
            resolve(true);
            close();
          },
        },
        {
          label: "Cancel",
          variant: "ghost",
          onClick: (close: Function) => {
            resolve(false);
            close();
          },
        },
      ],
    });
  });
};

onBeforeRouteLeave(async (to, from, next) => {
  if (isDirty.value) {
    const confirmed = await confirmLeave();
    if (confirmed) {
      next();
    } else {
      next(false);
    }
  } else {
    next();
  }
});
</script>
