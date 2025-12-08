<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="savedReplyData.title || __('New Saved Reply')"
          size="md"
          @click="goBack()"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-lg hover:opacity-70 !pr-0"
        />
        <Badge
          variant="subtle"
          theme="orange"
          size="sm"
          :label="__('Unsaved changes')"
          v-if="isDirty"
        />
      </div>
    </template>
    <template #header-actions>
      <div class="flex items-center gap-2">
        <Button
          :label="__('Preview')"
          size="sm"
          @click="onShowPreview()"
          icon-left="eye"
          :disabled="
            Boolean(!content?.editor?.state?.doc?.textContent?.trim()?.length)
          "
        />
        <Button
          :label="__('Save')"
          variant="solid"
          theme="gray"
          @click="onSave"
          :loading="isLoading"
          :disabled="Boolean(!isDirty)"
        />
      </div>
    </template>
    <template #content>
      <div
        v-if="getSavedReplyData.loading"
        class="flex items-center justify-center mt-12"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <div v-else class="flex flex-col gap-5">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div class="space-y-1.5">
            <FormControl
              :label="__('Name')"
              type="text"
              v-model="savedReplyData.title"
              required
              maxLength="50"
              @change="validateData('title')"
            />
            <ErrorMessage class="text-p-sm" :message="errors.title" />
          </div>
          <div class="space-y-1.5">
            <FormLabel :label="__('Scope')" />
            <Select
              v-model="savedReplyData.scope"
              :options="scopeDropdownOptions"
              required
            />
            <FormLabel
              :label="__('Choose who can view and use this response')"
            />
          </div>
        </div>
        <div v-if="savedReplyData.scope === 'Team'" class="space-y-1.5">
          <FormLabel :label="__('Teams')" required />
          <MultiSelect
            :options="teamsList"
            v-model="savedReplyData.teams"
            placeholder="Select teams"
            @update:modelValue="validateData('teams')"
          />
          <div class="text-xs text-ink-gray-5 cursor-default">
            {{ __("Restrict visibility to these teams") }}
          </div>
          <ErrorMessage class="text-p-sm" :message="errors.teams" />
        </div>
        <div class="space-y-1.5">
          <div class="flex items-center justify-between">
            <FormLabel :label="__('Response')" required />
            <DocumentationButton
              url="https://docs.frappe.io/helpdesk/saved-replies"
            />
          </div>
          <PreviewDialog v-model="previewDialog" />
          <TextEditor
            editor-class="!prose-sm max-w-full overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded-b border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors -mt-0.5"
            ref="content"
            :bubble-menu="false"
            :content="savedReplyData.response"
            @change="
              (val) => {
                savedReplyData.response = val;
                validateData('response');
              }
            "
            :fixed-menu="menuButtons"
            :extensions="[FieldAutocomplete]"
            :placeholder="'Hello {{ contact }}, \n\nWe are sorry for the inconvenience, we will get back to you soon. \n\nRegards, \n{{ full_name }}'"
          />
          <ErrorMessage class="text-p-sm" :message="errors.response" />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <ConfirmDialog
    v-model="showConfirmDialog.show"
    :title="showConfirmDialog.title"
    :message="showConfirmDialog.message"
    :onConfirm="showConfirmDialog.onConfirm"
    :onCancel="() => (showConfirmDialog.show = false)"
  />
</template>

<script setup lang="ts">
import {
  Badge,
  Button,
  call,
  createListResource,
  createResource,
  ErrorMessage,
  FormControl,
  FormLabel,
  LoadingIndicator,
  MultiSelect,
  Select,
  TextEditor,
  toast,
} from "frappe-ui";
import { computed, inject, onUnmounted, ref, watch } from "vue";
import { disableSettingModalOutsideClick } from "../settingsModal";
import { __ } from "@/translation";
import PreviewDialog from "./components/PreviewDialog.vue";
import { menuButtons } from "./savedReplies";
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import DocumentationButton from "@/components/DocumentationButton.vue";
import { storeToRefs } from "pinia";
import { useConfigStore } from "@/stores/config";
import { useAuthStore } from "@/stores/auth";
import { FieldAutocomplete } from "../../../tiptap-extensions";
import SettingsLayoutBase from "../../layouts/SettingsLayoutBase.vue";
import UserIcon from "~icons/lucide/user";
import UsersIcon from "~icons/lucide/users";
import GlobeIcon from "~icons/lucide/globe";

const showConfirmDialog = ref({
  show: false,
  title: "",
  message: "",
  onConfirm: () => {},
});

const savedRepliesActiveScreen = inject<any>("savedRepliesActiveScreen");
const previewDialog = ref({
  show: false,
  ticketId: "",
  savedReply: "",
  preview: null,
});
const content = ref();

const { teamRestrictionApplied } = storeToRefs(useConfigStore());
const { userTeams, isAdmin } = storeToRefs(useAuthStore());

const savedReplyData = ref({
  name: "",
  title: "",
  scope: "Personal",
  response: "",
  teams: [],
});
const isLoading = ref(false);
const initialData = ref("");
const errors = ref({
  title: "",
  response: "",
  teams: "",
});

const scopeDropdownOptions = computed(() => [
  {
    label: "Personal",
    value: "Personal",
    icon: UserIcon,
  },
  {
    label: "Team",
    value: "Team",
    icon: UsersIcon,
  },
  {
    label: "Global",
    value: "Global",
    icon: GlobeIcon,
  },
]);

const getSavedReplyData = createResource({
  url: "frappe.client.get",
  params: {
    doctype: "Email Template",
    name: savedRepliesActiveScreen.value.data?.name,
  },
  auto: false,
  onSuccess: (data) => {
    savedReplyData.value = {
      name: data.name,
      title: data.name,
      scope: data.scope,
      response: data.response,
      teams: data.teams?.map((team) => team.team) || [],
    };
    initialData.value = JSON.stringify(savedReplyData.value);
  },
});

const getTeamsListResource = createListResource({
  doctype: "HD Team",
  auto: true,
  fields: ["name"],
  start: 0,
  pageLength: 999,
  transform: (data) => {
    return data.map((item) => ({
      value: item.name,
      label: item.name,
    }));
  },
});

const teamsList = computed(() => {
  if (!isAdmin.value && teamRestrictionApplied.value) {
    return (
      userTeams.value?.map((team) => ({
        value: team,
        label: team,
      })) || []
    );
  }
  return getTeamsListResource.data || [];
});

const onShowPreview = () => {
  previewDialog.value.show = true;
  previewDialog.value.savedReply = savedReplyData.value.response;
};

if (savedRepliesActiveScreen.value.data?.name) {
  getSavedReplyData.submit();
} else {
  initialData.value = JSON.stringify(savedReplyData.value);
}

const isDirty = ref(false);

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
  // Workaround fix for settings modal not closing after going back
  setTimeout(() => {
    savedRepliesActiveScreen.value = {
      screen: "list",
      data: null,
    };
  }, 250);
  showConfirmDialog.value.show = false;
};

const onSave = () => {
  isLoading.value = true;
  validateData();

  if (Object.values(errors.value).some((e) => e)) {
    isLoading.value = false;
    toast.error(__("Please fill all the required fields"));
    return;
  }

  if (savedRepliesActiveScreen.value.data?.name) {
    updateSavedReply();
  } else {
    createSavedReply();
  }
};

const createSavedReply = () => {
  createResource({
    url: "frappe.client.insert",
    params: {
      doc: {
        doctype: "Email Template",
        name: savedReplyData.value.title,
        title: savedReplyData.value.title,
        subject: savedReplyData.value.title,
        response: savedReplyData.value.response,
        scope: savedReplyData.value.scope,
        teams: savedReplyData.value.teams.map((team) => ({
          team: team,
        })),
        reference_doctype: "HD Ticket",
      },
    },
    auto: true,
    onSuccess: (data) => {
      toast.success(__("Saved reply saved"));
      isLoading.value = false;
      savedReplyData.value = {
        ...savedReplyData.value,
        name: data.name,
      };
      initialData.value = JSON.stringify(savedReplyData.value);
      savedRepliesActiveScreen.value = {
        screen: "view",
        data: { name: data.name },
      };
    },
  }).promise.catch(() => {
    isLoading.value = false;
  });
};

const updateSavedReply = async () => {
  let renameError = false;

  if (savedReplyData.value.name !== savedReplyData.value.title) {
    await call("frappe.client.rename_doc", {
      doctype: "Email Template",
      old_name: savedReplyData.value.name,
      new_name: savedReplyData.value.title,
    })
      .then(() => {
        savedReplyData.value = {
          ...savedReplyData.value,
          name: savedReplyData.value.title,
        };
      })
      .catch(async (er) => {
        const error =
          er?.messages?.[0] ||
          __("Some error occurred while renaming saved reply");
        toast.error(error);
        isLoading.value = false;
        renameError = true;
      });
  }
  if (renameError) return;

  createResource({
    url: "frappe.client.set_value",
    params: {
      doctype: "Email Template",
      name: savedReplyData.value.name,
      fieldname: {
        name: savedReplyData.value.title,
        title: savedReplyData.value.title,
        subject: savedReplyData.value.title,
        response: savedReplyData.value.response,
        scope: savedReplyData.value.scope,
        teams: savedReplyData.value.teams.map((team) => ({
          team: team,
        })),
      },
    },
    auto: true,
    onSuccess: () => {
      isDirty.value = false;
      isLoading.value = false;
      disableSettingModalOutsideClick.value = false;
      toast.success(__("Saved reply updated"));
    },
  });
};

const validateData = (key?: string) => {
  const validateField = (key) => {
    switch (key) {
      case "title":
        if (!savedReplyData.value.title) {
          errors.value.title = __("Title is required");
        } else {
          errors.value.title = "";
        }
        break;

      case "response":
        if (!content.value?.editor?.state?.doc?.textContent?.trim()?.length) {
          errors.value.response = __("Response is required");
        } else {
          errors.value.response = "";
        }
        break;

      case "teams":
        if (
          savedReplyData.value.scope === "Team" &&
          !savedReplyData.value.teams.length
        ) {
          errors.value.teams = __("At least one team is required");
        } else {
          errors.value.teams = "";
        }
        break;

      default:
        break;
    }
  };
  if (key) {
    validateField(key);
  } else {
    (Object.keys(errors.value) as string[]).forEach(validateField);
  }

  return errors.value;
};

watch(
  savedReplyData,
  (newVal) => {
    if (!initialData.value) return;
    isDirty.value = JSON.stringify(newVal) != initialData.value;
    if (isDirty.value) {
      disableSettingModalOutsideClick.value = true;
    } else {
      disableSettingModalOutsideClick.value = false;
    }
  },
  { deep: true }
);

onUnmounted(() => {
  disableSettingModalOutsideClick.value = false;
});
</script>
