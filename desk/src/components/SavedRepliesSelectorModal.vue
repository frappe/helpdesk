<template>
  <Dialog
    v-model="show"
    :options="{
      size: '4xl',
    }"
    @vue:unmounted="resetFilter"
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
            <div class="relative w-full">
              <Input
                ref="searchInput"
                :model-value="search"
                @input="search = $event"
                :placeholder="__('Search')"
                type="text"
                class="bg-white hover:bg-white focus:ring-0 border-outline-gray-2"
                icon-left="search"
                debounce="300"
                inputClass="p-4 pr-12"
              />
              <Button
                v-if="search"
                icon="x"
                variant="ghost"
                @click="search = ''"
                class="absolute right-1 top-1/2 -translate-y-1/2"
              />
            </div>
            <Dropdown :options="filters" placement="right">
              <Button :label="activeFilter" icon-left="filter" class="p-4" />
            </Dropdown>
          </div>
        </div>
        <div class="px-4 h-full overflow-y-auto">
          <div
            v-if="savedReplyListResource?.list?.loading"
            class="flex items-center justify-center mt-24"
          >
            <LoadingIndicator class="size-4" />
          </div>
          <div
            v-if="
              !savedReplyListResource?.list?.loading &&
              savedReplyListResource?.data?.length
            "
            class="grid grid-cols-1 md:grid-cols-3 gap-2 pb-36"
          >
            <div
              v-for="template in savedReplyListResource?.data"
              :key="template.name"
              class="flex h-56 cursor-pointer flex-col gap-2 rounded-lg border p-3 hover:bg-gray-100 relative"
              @click="onTemplateSelect(template)"
            >
              <div class="text-base font-semibold truncate border-b pb-2">
                {{ template.title }}
              </div>
              <TextEditor
                v-if="template.message"
                :content="template.message"
                :editable="false"
                editor-class="!prose-sm max-w-none !text-sm text-gray-600 focus:outline-none"
                class="flex-1 overflow-hidden pointer-events-none"
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
          <div
            v-if="
              !savedReplyListResource?.list?.loading &&
              !savedReplyListResource?.data?.length
            "
            class="mt-2"
          >
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
  Input,
  LoadingIndicator,
  TextEditor,
  createListResource,
  createResource,
  Dialog,
} from "frappe-ui";
import { ref, computed, nextTick, watch, onUnmounted } from "vue";
import {
  setActiveSettingsTab,
  showSettingsModal,
} from "./Settings/settingsModal";
import { showEmailBox } from "../pages/ticket/modalStates";
import { useStorage } from "@vueuse/core";
import { SavedReply } from "@/types";
import { storeToRefs } from "pinia";
import { useConfigStore } from "@/stores/config";
import { __ } from "@/translation";

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
const activeFilter = useStorage("saved-replies-filter", "Personal");
const { disableGlobalScopeForSavedReplies, teamRestrictionApplied } =
  storeToRefs(useConfigStore());

const filters = computed(() => {
  const options = [
    {
      label: __("All"),
      value: "All",
      onClick: () => (activeFilter.value = "All"),
    },
    {
      label: __("Personal"),
      value: "Personal",
      onClick: () => (activeFilter.value = "Personal"),
    },
    {
      label: __("My Team"),
      value: "Team",
      onClick: () => (activeFilter.value = "My Team"),
    },
    {
      label: __("Global"),
      value: "Global",
      onClick: () => (activeFilter.value = "Global"),
    },
  ];
  if (teamRestrictionApplied.value && disableGlobalScopeForSavedReplies.value) {
    options.pop();
  }
  return options;
});

// Set default filter to Personal if Global is disabled
if (
  teamRestrictionApplied.value &&
  disableGlobalScopeForSavedReplies.value &&
  activeFilter.value == "Global"
) {
  activeFilter.value = "Personal";
}

const emit = defineEmits(["apply"]);

const search = ref("");
const searchInput = ref<InstanceType<typeof Input>>();
const selectedTemplate = ref({
  name: "",
  isLoading: false,
});

const scope = computed(() => {
  return filters.value.find((f) => f.label === activeFilter.value)?.value;
});

const savedReplyListResource = createListResource({
  doctype: "HD Saved Reply",
  fields: ["name", "title", "owner", "scope", "message"],
  filters: {
    scope: scope.value == "All" ? undefined : ["=", scope.value],
  },
  cache: ["SavedReplyListForModal"],
  auto: true,
  orderBy: "modified desc",
  start: 0,
  pageLength: 999,
});

onUnmounted(() => {
  showEmailBox.value = true;
});

const onTemplateSelect = (template: SavedReply) => {
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
    onSuccess: (data: string) => {
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

const resetFilter = () => {
  savedReplyListResource.filters = {
    ...savedReplyListResource.filters,
    title: undefined,
  };
};

watch(search, (newValue) => {
  savedReplyListResource.filters = {
    ...savedReplyListResource.filters,
    title: ["like", `%${newValue}%`],
  };
  savedReplyListResource.list.reload();
});

watch(activeFilter, () => {
  savedReplyListResource.filters = {
    ...savedReplyListResource?.filters,
    scope: scope.value == "All" ? undefined : ["=", scope.value],
  };
  savedReplyListResource.list.reload();
});

watch(
  show,
  (newValue) => {
    if (newValue) {
      nextTick(() => {
        const inputEl = searchInput.value?.$el?.querySelector("input");
        inputEl?.focus();
      });
    }
  },
  { immediate: true }
);
</script>
