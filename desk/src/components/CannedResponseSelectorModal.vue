<template>
  <Dialog
    v-model="show"
    :options="{
      title: 'Canned Responses',
      size: '4xl',
    }"
  >
    <template #body-content>
      <div class="flex items-center gap-2">
        <TextInput
          class="w-full"
          ref="searchInput"
          v-model="search"
          type="text"
          :placeholder="'Site Down'"
        >
          <template #prefix>
            <FeatherIcon name="search" class="h-4 w-4 text-gray-500" />
          </template>
        </TextInput>
        <Popover placement="bottom-end">
          <template #target="{ togglePopover }">
            <Button label="Teams" icon-left="filter" @click="togglePopover()">
              <template #suffix>
                <div
                  class="flex items-center rounded-full bg-gray-300 justify-center text-xs size-5"
                >
                  {{ teamsList.length }}
                </div>
              </template>
            </Button>
          </template>
          <template #body-main>
            <div class="p-2 text-ink-gray-9 w-52 overflow-y-auto max-h-60">
              <div
                v-for="team in teamsListResource.data"
                :key="team.name"
                class="p-2 cursor-pointer hover:bg-gray-50 text-base flex items-center justify-between rounded select-none"
                @click="toggleTeamToFilter(team.name)"
              >
                <span class="truncate">
                  {{ team.name }}
                </span>
                <FeatherIcon
                  v-if="isTeamInFilter(team.name)"
                  name="check"
                  class="size-4"
                />
              </div>
            </div>
          </template>
        </Popover>
      </div>
      <div
        v-if="filteredTemplates.length"
        class="mt-2 grid max-h-[560px] grid-cols-1 md:grid-cols-3 gap-2 overflow-y-auto"
      >
        <div
          v-for="template in filteredTemplates"
          :key="template.name"
          class="flex h-56 cursor-pointer flex-col gap-2 rounded-lg border p-3 hover:bg-gray-100 relative"
          @click="onTemplateSelect(template)"
        >
          <div class="flex flex-col pb-2 border-b gap-0.5">
            <div class="text-base font-semibold truncate">
              {{ template.name }}
            </div>
            <div class="text-xs text-gray-500 truncate">
              {{ template.teams?.join(", ") || "No team" }}
            </div>
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
          <div class="text-lg text-gray-500">
            {{ "No templates found" }}
          </div>
        </div>
      </div>
      <div class="flex justify-end mt-4">
        <Button label="New Canned Response" @click="onNewCannedResponseClick" />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import {
  FeatherIcon,
  LoadingIndicator,
  Popover,
  TextEditor,
  createListResource,
  createResource,
} from "frappe-ui";
import { ref, computed, nextTick, watch, onUnmounted } from "vue";
import {
  setActiveSettingsTab,
  showSettingsModal,
} from "./Settings/settingsModal";
import { useAuthStore } from "@/stores/auth";
import { storeToRefs } from "pinia";
import { showEmailBox } from "@/pages/ticket/modalStates";

const auth = storeToRefs(useAuthStore());

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
const teamsList = ref([...auth.userTeams.value, "No team"]);

const teamsListResource = createListResource({
  doctype: "HD Team",
  fields: ["name"],
  auto: true,
  transform: (data) => {
    return [{ name: "No team" }, ...data];
  },
});

const isTeamInFilter = (teamName: string) => {
  return teamsList.value.includes(teamName);
};

const toggleTeamToFilter = (teamName: string) => {
  if (teamsList.value.includes(teamName)) {
    teamsList.value = teamsList.value.filter((team) => team !== teamName);
  } else {
    teamsList.value = [...teamsList.value, teamName];
  }
};

watch(teamsList, () => {
  cannedResponsesResource.reload({
    teams: teamsList.value,
  });
});

const emit = defineEmits(["apply"]);

const search = ref("");
const cannedResponsesList = ref([]);
const selectedTemplate = ref({
  name: "",
  isLoading: false,
});

const cannedResponsesResource = createResource({
  url: "helpdesk.api.canned_response.get_canned_responses",
  params: {
    teams: ["No team"],
  },
  onSuccess: (data) => {
    cannedResponsesList.value = data;
  },
  auto: true,
});

onUnmounted(() => {
  showEmailBox.value = true;
});

const filteredTemplates = computed(() => {
  return (
    cannedResponsesList.value?.filter((template) => {
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
    url: "helpdesk.api.canned_response.get_rendered_canned_response",
    params: {
      canned_response_id: template.name,
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

const onNewCannedResponseClick = () => {
  show.value = false;
  showSettingsModal.value = true;
  setActiveSettingsTab("Canned Responses");
};

watch(show, (value) => {
  if (value) {
    // @ts-ignore
    nextTick(() => searchInput.value?.el?.focus());
    cannedResponsesResource.reload();
  }
});
</script>
