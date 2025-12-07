<template>
  <Dialog
    v-model="show"
    :options="{
      size: '4xl',
    }"
  >
    <template #body>
      <div class="max-h-[575px]" :style="{ height: 'calc(100vh - 8rem)' }">
        <div class="flex items-center justify-between w-full p-4 pb-2">
          <div class="text-2xl font-semibold">{{ __("Saved Replies") }}</div>
          <Button
            variant="solid"
            icon-left="plus"
            :label="__('New')"
            @click="onNewSavedReplyClick"
          />
        </div>
        <div class="p-4">
          <div class="flex items-center gap-2">
            <TextInput
              class="w-full"
              ref="searchInput"
              v-model="search"
              type="text"
              :placeholder="__('Site Down')"
            >
              <template #prefix>
                <FeatherIcon name="search" class="h-4 w-4 text-gray-500" />
              </template>
            </TextInput>
            <Dropdown :options="filters" placement="right">
              <Button :label="activeFilter" icon-left="filter" />
            </Dropdown>
          </div>
        </div>
        <div class="px-4 h-full overflow-y-auto">
          <div
            v-if="filteredTemplates.length"
            class="grid grid-cols-1 md:grid-cols-3 gap-2 pb-36"
          >
            <div
              v-for="template in filteredTemplates"
              :key="template.name"
              class="flex h-56 cursor-pointer flex-col gap-2 rounded-lg border p-3 hover:bg-gray-100 relative"
              @click="onTemplateSelect(template)"
            >
              <div class="text-base font-semibold truncate border-b pb-2">
                {{ template.name }}
              </div>
              <TextEditor
                v-if="template.response"
                :content="template.response"
                :editable="false"
                editor-class="!prose-sm max-w-none !text-sm text-gray-600 focus:outline-none"
                class="flex-1 overflow-hidden"
              />
              <div
                v-if="
                  selectedTemplate.name === template.name &&
                  selectedTemplate.isLoading
                "
                class="flex items-center justify-center absolute top-0 left-0 w-full h-full bg-black/20 rounded-lg"
              >
                <LoadingIndicator class="size-4" />
              </div>
            </div>
          </div>
          <div v-else class="mt-2">
            <div class="flex h-56 flex-col items-center justify-center">
              <div class="text-p-sm text-gray-500">
                {{ __("No Saved Replies found") }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import {
  Button,
  Dropdown,
  FeatherIcon,
  LoadingIndicator,
  TextEditor,
  createResource,
} from "frappe-ui";
import { ref, computed, nextTick, watch, onUnmounted } from "vue";
import {
  setActiveSettingsTab,
  showSettingsModal,
} from "./Settings/settingsModal";
import { showEmailBox } from "../pages/ticket/modalStates";
import { useStorage } from "@vueuse/core";

const props = defineProps({
  doctype: {
    type: String,
    default: "",
  },
  ticketId: {
    type: String,
    default: "",
  },
});

const show = defineModel();
const searchInput = ref("");
const activeFilter = useStorage("saved-replies-filter", "Personal");

const filters = computed(() => [
  {
    label: "Global",
    onClick: () => (activeFilter.value = "Global"),
  },
  {
    label: "My Team",
    onClick: () => (activeFilter.value = "My Team"),
  },
  {
    label: "Personal",
    onClick: () => (activeFilter.value = "Personal"),
  },
]);

watch(activeFilter, () => {
  getSavedRepliesResource.reload({
    scope: activeFilter.value,
  });
});

const emit = defineEmits(["apply"]);

const search = ref("");
const savedRepliesList = ref([]);
const selectedTemplate = ref({
  name: "",
  isLoading: false,
});

const getSavedRepliesResource = createResource({
  url: "helpdesk.api.saved_replies.get_saved_replies",
  params: {
    scope: activeFilter.value,
  },
  onSuccess: (data) => {
    savedRepliesList.value = data;
  },
  auto: true,
});

onUnmounted(() => {
  showEmailBox.value = true;
});

const filteredTemplates = computed(() => {
  return (
    savedRepliesList.value?.filter((template) => {
      return (
        template.name.toLowerCase().includes(search.value.toLowerCase()) ||
        template.subject.toLowerCase().includes(search.value.toLowerCase())
      );
    }) ?? []
  );
});

const onTemplateSelect = (template) => {
  if (selectedTemplate.value.isLoading) return;
  selectedTemplate.value = {
    name: template.name,
    isLoading: true,
  };
  const renderResponse = createResource({
    url: "helpdesk.api.saved_replies.get_rendered_saved_reply",
    params: {
      saved_reply_id: template.name,
      ticket_id: props.ticketId,
    },
    onSuccess: (data) => {
      selectedTemplate.value = {
        name: "",
        isLoading: false,
      };
      emit("apply", data);
    },
  });
  renderResponse.submit().catch(() => {
    selectedTemplate.value = {
      name: "",
      isLoading: false,
    };
  });
};

const onNewSavedReplyClick = () => {
  show.value = false;
  showSettingsModal.value = true;
  setActiveSettingsTab("Saved Replies");
};

watch(show, (value) => {
  if (value) {
    // @ts-ignore
    nextTick(() => searchInput.value?.el?.focus());
    getSavedRepliesResource.reload();
  }
});
</script>
