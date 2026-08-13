<template>
  <Dialog v-model:open="show" size="4xl" bare @after-leave="onAfterLeave">
    <template #default>
      <div class="max-h-[575px]" :style="{ height: 'calc(100vh - 8rem)' }">
        <div class="flex items-center justify-between w-full p-4 pb-2">
          <div class="text-3xl-semibold">{{ __("Saved Replies") }}</div>
          <Button
            icon-left="lucide-plus"
            :label="__('New')"
            @click="onNewSavedReplyClick"
          />
        </div>
        <div class="p-4">
          <div class="flex items-center gap-2">
            <div class="relative w-full">
              <TextInput
                ref="searchInput"
                :model-value="search"
                @update:model-value="search = $event"
                :placeholder="__('Search')"
                type="text"
                class="focus:ring-0 border-outline-gray-2"
                :debounce="300"
                autofocus
              >
                <template #prefix>
                  <LucideSearch class="size-4" />
                </template>
              </TextInput>
              <Button
                v-if="search"
                icon="lucide-x"
                variant="ghost"
                @click="search = ''"
                class="absolute end-1 top-1/2 -translate-y-1/2"
              />
            </div>
            <Dropdown :options="filters" placement="right">
              <Button :label="activeFilterLabel">
                <template #prefix><FilterIcon class="h-4" /></template>
              </Button>
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
            class="grid grid-cols-1 md:grid-cols-3 gap-3 pb-36"
          >
            <div
              v-for="template in savedReplyListResource?.data"
              :key="template.name"
              class="flex h-56 cursor-pointer flex-col gap-2 rounded-lg border border-outline-gray-1 bg-surface-base p-3 hover:border-outline-gray-3 relative"
              @click="onTemplateSelect(template)"
            >
              <div class="flex items-center gap-2 border-b pb-2">
                <div class="text-base-semibold truncate max-w-[75%]">
                  {{ template.title }}
                </div>
                <Tooltip
                  v-if="actionCounts[template.name]"
                  :text="actionTooltip(actionCounts[template.name])"
                >
                  <Badge
                    class="ms-auto shrink-0"
                    theme="gray"
                    variant="subtle"
                    :label="actionLabel(actionCounts[template.name])"
                  />
                </Tooltip>
              </div>
              <div
                v-if="template.message"
                class="flex-1 overflow-hidden pointer-events-none [mask-image:linear-gradient(to_bottom,black_80%,transparent)]"
              >
                <Editor
                  :model-value="template.message"
                  :extensions="extensions"
                  :editable="false"
                >
                  <template #default>
                    <EditorContent
                      class="max-w-none text-p-sm text-ink-gray-5 focus:outline-none"
                    />
                  </template>
                </Editor>
              </div>
              <div
                v-if="
                  selectedTemplate.name === template.name &&
                  selectedTemplate.isLoading
                "
                class="flex items-center justify-center absolute top-0 start-0 w-full h-full rounded-lg"
              >
                <LoadingIndicator class="size-4" />
              </div>
            </div>
            <div class="col-span-full flex justify-center">
              <Button
                v-if="
                  !savedReplyListResource.list.loading &&
                  savedReplyListResource.hasNextPage
                "
                :label="__('Load More')"
                icon-left="lucide-refresh-cw"
                @click="savedReplyListResource.next()"
              />
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
              <div class="text-p-sm text-ink-gray-4">
                {{ __("No saved replies found") }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { recordSavedReplyUse } from "@/components/command-palette/savedReplyCommands";
import { buildEditorExtensions } from "@/components/editor/config";
import FilterIcon from "@/components/icons/FilterIcon.vue";
import { useConfigStore } from "@/stores/config";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { RenderedSavedReply, SavedReply } from "@/types";
import { useStorage } from "@vueuse/core";
import {
  Badge,
  Button,
  createListResource,
  createResource,
  Dialog,
  Dropdown,
  LoadingIndicator,
  TextInput,
  Tooltip,
} from "frappe-ui";
import { Editor, EditorContent } from "frappe-ui/editor";
import { storeToRefs } from "pinia";
import { computed, h, nextTick, ref, watch } from "vue";
import {
  setActiveSettingsTab,
  showSettingsModal,
} from "./Settings/settingsModal";
const extensions = buildEditorExtensions();

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
  const scopes = [
    { label: __("All"), value: "All" },
    { label: __("Personal"), value: "Personal" },
    { label: __("My Team(s)"), value: "Team" },
    { label: __("Global"), value: "Global" },
  ];
  if (teamRestrictionApplied.value && disableGlobalScopeForSavedReplies.value) {
    scopes.pop();
  }
  return scopes.map((scope) => ({
    ...scope,
    selected: activeFilter.value === scope.value,
    onClick: () => (activeFilter.value = scope.value),
    slots: {
      suffix: () =>
        h(
          "span",
          { class: "text-sm text-ink-gray-5" },
          String(scopeCounts.data?.[scope.value] ?? 0)
        ),
    },
  }));
});

const activeFilterLabel = computed(() => {
  return (
    filters.value.find((filter) => filter.value === activeFilter.value)
      ?.label ?? activeFilter.value
  );
});

// Older sessions stored the label instead of the value
if (activeFilter.value == "My Team") {
  activeFilter.value = "Team";
}

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
const searchInput = ref<InstanceType<typeof TextInput>>();
const selectedTemplate = ref({
  name: "",
  isLoading: false,
});
const pendingTemplate = ref<RenderedSavedReply | null>(null);

function onAfterLeave() {
  if (pendingTemplate.value !== null) {
    emit("apply", pendingTemplate.value);
    pendingTemplate.value = null;
  }
}

const scope = computed(() => {
  return filters.value.find((f) => f.value === activeFilter.value)?.value;
});

const savedReplyListResource = createListResource({
  doctype: "HD Saved Reply",
  fields: ["name", "title", "owner", "scope", "message", "actions"],
  filters: {
    scope: scope.value == "All" ? undefined : ["=", scope.value],
  },
  cache: ["SavedReplyListForModal"],
  auto: true,
  orderBy: "modified desc",
  start: 0,
  pageLength: 20,
});

// One grouped query answers every scope at once, so the menu can say where the
// replies live before an agent switches to find out
const scopeCounts = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "HD Saved Reply",
    fields: ["scope", { COUNT: "name" }],
    group_by: "scope",
    limit_page_length: 0,
  },
  transform: (rows: { scope: string }[]) => {
    const counts: Record<string, number> = { All: 0 };
    for (const row of rows) {
      const count = row["COUNT(`name`)"] ?? 0;
      counts[row.scope] = count;
      counts.All += count;
    }
    return counts;
  },
});

const actionCounts = computed<Record<string, number>>(() => {
  const counts: Record<string, number> = {};
  for (const row of savedReplyListResource.data || []) {
    counts[row.name] = JSON.parse(row.actions || "[]").length;
  }
  return counts;
});

const actionLabel = (count: number) =>
  count === 1 ? __("1 action") : __("{0} actions", count);

const actionTooltip = (count: number) =>
  count === 1
    ? __("Applies 1 action when sent")
    : __("Applies {0} actions when sent", count);

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
    onSuccess: (data: RenderedSavedReply) => {
      selectedTemplate.value = {
        name: "",
        isLoading: false,
      };
      // If user cancelled (Escape/outside click) while API was in flight, discard
      if (!show.value) return;
      pendingTemplate.value = data;
      show.value = false;
      // Shared with the palette: modal picks count toward its most-used rows.
      recordSavedReplyUse(template.name, template.title);
      capture("saved_reply_applied", { data: { source: "composer" } });
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

// A reply is as findable by its wording as by its name, now that only a page loads
watch(search, (query) => {
  savedReplyListResource.orFilters = query
    ? { title: ["like", `%${query}%`], message: ["like", `%${query}%`] }
    : undefined;
  savedReplyListResource.start = 0;
  savedReplyListResource.list.reload();
});

watch(activeFilter, () => {
  savedReplyListResource.filters = {
    ...savedReplyListResource?.filters,
    scope: scope.value == "All" ? undefined : ["=", scope.value],
  };
  savedReplyListResource.start = 0;
  savedReplyListResource.list.reload();
});

watch(
  show,
  (newValue) => {
    if (!newValue) return;
    if (search.value) {
      search.value = "";
    } else {
      savedReplyListResource.list.reload();
    }
    // Counts don't move with the selected scope, so this is the only refetch
    scopeCounts.reload();
    nextTick(() => {
      const inputEl = searchInput.value?.$el?.querySelector("input");
      inputEl?.focus();
    });
  },
  { immediate: true }
);
</script>
