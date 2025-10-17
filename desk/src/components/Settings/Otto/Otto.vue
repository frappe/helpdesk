<template>
  <!-- Main Settings View -->
  <SettingsView
    v-if="currentView === 'main'"
    title="Otto"
    description="Configure Otto settings to enable smart features."
    :isDirty="isAnyDirty"
    :isSaving="isSaving"
    :showSaveButton="true"
    @save="save"
  >
    <LoadingIndicator v-if="canUseOtto.loading || hdSettings.loading" />

    <!-- Warning if Otto is not installed -->
    <div
      v-if="canUseOtto.data === false"
      class="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6"
    >
      <div class="flex items-start gap-3">
        <div>
          <p class="text-sm font-medium text-amber-900">
            Otto is not installed
          </p>
          <p class="text-sm text-amber-700 mt-1">
            <!-- TODO: add docs link to enable OTTO Integration -->
            Please install <a href="#" class="underline">Otto</a> to enable
            smart features.
          </p>
        </div>
      </div>
    </div>

    <!-- Enable Otto Section -->
    <div v-if="canUseOtto.data && hdSettings.doc" class="mb-6">
      <Checkbox
        label="Enable Smart Features"
        title="Enable or disable smart features for Helpdesk."
        v-model="hdSettings.doc.enable_smart_features"
        @update:modelValue="
          hdSettings.doc.enable_smart_features = $event ? 1 : 0
        "
      />
      <div class="text-p-xs text-ink-gray-6 mt-1">
        Enable or disable smart features for Helpdesk.
      </div>
    </div>

    <!-- API Keys Section -->
    <LoadingIndicator v-if="getKeysSet.loading" />

    <div
      v-if="
        canUseOtto.data &&
        hdSettings.doc.enable_smart_features &&
        getKeysSet.data
      "
      class="mt-6"
    >
      <div class="text-base font-semibold text-ink-gray-8">API Keys</div>
      <div class="text-p-xs text-ink-gray-6 mt-1">
        Configure API keys for LLM providers. API key is used only if a model is
        selected to be used for a feature.
        <span
          class="text-ink-blue-6 cursor-pointer underline"
          @click="currentView = 'models'"
          >View models</span
        >
      </div>
      <div class="grid grid-cols-2 gap-4 mt-4">
        <Password
          label="Anthropic API Key"
          v-model="apiKeys.Anthropic"
          :placeholder="'sk-ant-...'"
        />
        <Password
          label="OpenAI API Key"
          v-model="apiKeys.OpenAI"
          :placeholder="'sk-...'"
        />
        <Password
          label="Gemini API Key (Google)"
          v-model="apiKeys.Google"
          :placeholder="'...'"
        />
      </div>

      <div
        v-if="
          Object.keys(getKeysSet.data ?? {}).every(
            (key) => !getKeysSet.data[key]
          )
        "
        class="text-p-xs text-ink-red-4 mt-4"
      >
        At least one API key must be set for smart features to work.
      </div>
    </div>

    <!-- Features Section -->
    <div
      v-if="canUseOtto.data && hdSettings.doc?.enable_smart_features"
      class="mt-6"
    >
      <div class="text-base font-semibold text-ink-gray-8">Features</div>
      <div class="text-p-xs text-ink-gray-6 mt-1">
        Configure Otto enabled smart features.
      </div>

      <div class="flex items-center justify-between p-3 rounded relative mt-2">
        <div class="flex flex-col gap-1">
          <h2
            class="text-base font-medium text-ink-gray-7 relative z-10 pointer-events-none flex items-center gap-2"
          >
            Activity Summarization
            <div
              v-if="!modelMap[featureConfig.summary.llm]?.is_api_key_set"
              class="w-1 h-1 rounded-full bg-red-500 inline-block"
            ></div>
          </h2>
          <p
            class="text-sm text-ink-gray-5 truncate relative z-10 pointer-events-none"
          >
            Generate summary of ticket activity on demand.
          </p>
        </div>
        <FeatherIcon
          name="chevron-right"
          class="text-ink-gray-7 size-4 relative z-10 pointer-events-none"
        />
        <button
          type="button"
          class="w-full h-full absolute top-0 left-0 hover:bg-gray-50 rounded-[inherit]"
          @click="openSummarySettings"
        >
          <span class="sr-only">{{
            __("configure activity summarization")
          }}</span>
        </button>
      </div>
    </div>
  </SettingsView>

  <!-- Models View -->
  <SettingsView
    v-else-if="currentView === 'models'"
    title="Models"
    description="View available models."
    :isDirty="isAnyDirty"
    :isSaving="isSaving"
    :showBackButton="true"
    :showSaveButton="false"
    @back="currentView = 'main'"
  >
    <LoadingIndicator v-if="getModels.loading" />
    <ModelList v-else :models="getModels.data ?? []" />
  </SettingsView>

  <!-- Summary Settings View -->
  <SettingsView
    v-else-if="currentView === 'summary'"
    v-model="featureConfig.summary.enabled"
    title="Activity Summarization"
    description="Configure activity summarization."
    :isDirty="isAnyDirty"
    :isSaving="isSaving"
    :showEnabledSwitch="true"
    :showBackButton="true"
    :showSaveButton="true"
    @back="currentView = 'main'"
    @save="save"
  >
    <LoadingIndicator v-if="getFeatureConfig.loading" />
    <div v-else>
      <!-- Model Selection -->
      <div v-if="featureConfig.summary.enabled" class="mb-6">
        <FormControl
          type="select"
          label="Select a model"
          v-model="featureConfig.summary.llm"
          :options="
            getModels.data
              ?.filter((model) => model.is_enabled)
              .map((model) => ({
                label: model.title,
                value: model.name,
              }))
              .sort((a, b) => a.label.localeCompare(b.label)) ?? []
          "
        />
        <div class="text-p-xs text-ink-gray-6 mt-1">
          LLM to use for activity summarization.
        </div>

        <div
          v-if="!modelMap[featureConfig.summary.llm]?.is_api_key_set"
          class="text-p-xs text-ink-red-4 mt-1"
        >
          API key not set for this model, feature will not work.
          <span class="cursor-pointer underline" @click="currentView = 'models'"
            >View models</span
          >
        </div>
      </div>

      <!-- Guidelines/Prompt -->
      <div v-if="featureConfig.summary.enabled" class="mb-6">
        <Textarea
          class="text-p-sm [&>textarea]:font-mono"
          label="Guidelines"
          v-model="featureConfig.summary.guidelines"
          placeholder="Enter custom instructions for summary generation..."
          :rows="12"
        />
        <div class="mt-1 flex justify-between items-start">
          <p class="text-p-xs text-ink-gray-6 m-0 p-0">
            Guidelines such as style, format, etc to be followed.
          </p>

          <Button
            v-if="getDefaultSummaryConfig.data"
            class="w-fit"
            :disabled="
              featureConfig.summary.guidelines ===
              getDefaultSummaryConfig.data?.guidelines
            "
            type="button"
            size="sm"
            variant="subtle"
            @click="
              featureConfig.summary.guidelines =
                getDefaultSummaryConfig.data?.guidelines
            "
          >
            {{ __("Reset Content") }}
          </Button>
        </div>
      </div>
    </div>
  </SettingsView>
</template>

<script setup lang="ts">
import Password from "@/components/Password.vue";
import {
  Checkbox,
  FormControl,
  LoadingIndicator,
  Textarea,
  createDocumentResource,
  createResource,
  toast,
} from "frappe-ui";
import { computed, ref, watch } from "vue";
import { isDocDirty } from "../Telephony/utils";
import SettingsView from "./SettingsView.vue";
import type { SmartFeatureConfig } from "./types";
import ModelList from "./ModelList.vue";

type ViewType = "main" | "summary" | "models";

const currentView = ref<ViewType>("main");

const dummyKey = "*********************************";

const apiKeys = ref({
  OpenAI: "",
  Anthropic: "",
  Google: "",
});

const isDirty = ref({
  hdSettings: false,
  apiKeys: false,
  featureConfig: false,
});
const isSaving = ref(false);

const featureConfig = ref<SmartFeatureConfig>({
  summary: {
    llm: "",
    enabled: false,
    guidelines: "",
  },
});

const originalConfig = ref<SmartFeatureConfig | null>(null);

const hdSettings = createDocumentResource({
  doctype: "HD Settings",
  name: "HD Settings",
  fields: ["enable_smart_features"],
  auto: true,
});
const setApiKeys = createResource({ url: "otto.lib.model.set_api_keys" });
const setFeatureConfig = createResource({
  url: "helpdesk.api.otto.set_feature_config",
});
const canUseOtto = createResource({
  url: "helpdesk.api.otto.can_use_otto",
  auto: true,
  onSuccess: (data) => {
    if (!data) return;
    getKeysSet.reload();
    getFeatureConfig.reload();
    getModels.reload();
    getDefaultSummaryConfig.reload();
  },
});
const getModels = createResource({
  url: "otto.lib.model.get_models",
  params: { get_details: true, include_unavailable: true },
});
const getKeysSet = createResource({
  url: "otto.lib.model.get_keys_set",
  onSuccess: (data) => {
    for (const k in data) {
      if (!data[k]) continue;
      apiKeys.value[k] = dummyKey;
    }
  },
});
const getFeatureConfig = createResource({
  url: "helpdesk.api.otto.get_feature_config",
  onSuccess: (data) => {
    originalConfig.value = data;

    if (data.summary) {
      featureConfig.value.summary.llm = data.summary?.llm ?? "";
      featureConfig.value.summary.enabled = data.summary?.enabled ?? false;
      featureConfig.value.summary.guidelines = data.summary?.guidelines ?? "";
    }
  },
  onError: () => {
    toast.error("Failed to load summary settings");
  },
});
const getDefaultSummaryConfig = createResource({
  url: "helpdesk.api.otto.summary.get_default_summary_config",
});
const modelMap = computed(() => {
  if (!getModels.data) return {};

  return getModels.data.reduce((acc, model) => {
    acc[model.name] = model;
    return acc;
  }, {} as Record<string, unknown>);
});

const isAnyDirty = computed(
  () =>
    isDirty.value.hdSettings ||
    isDirty.value.apiKeys ||
    isDirty.value.featureConfig
);

async function save() {
  isSaving.value = true;
  const promises = [];

  // Save main settings
  if (isDirty.value.hdSettings) {
    promises.push(
      hdSettings.save.submit().catch((er) => {
        const error = `HD Settings error: ${er?.messages?.[0]}`;
        toast.error(error || "Failed to save HD Settings");
      })
    );
  }

  if (isDirty.value.apiKeys) {
    const keysToSave: Record<string, string> = {};
    for (const key in apiKeys.value) {
      if (apiKeys.value[key] === dummyKey && (getKeysSet.data ?? {})[key])
        continue;
      if (!apiKeys.value[key] && !(getKeysSet.data ?? {})[key]) continue;
      keysToSave[key] = apiKeys.value[key];
    }

    if (Object.keys(keysToSave).length > 0) {
      promises.push(
        setApiKeys.submit({ keys: keysToSave }).catch((er) => {
          const error = `API Keys error: ${er?.messages?.[0]}`;
          toast.error(error || "Failed to save API keys");
        })
      );
    }
  }

  if (isDirty.value.featureConfig) {
    const config = JSON.parse(JSON.stringify(featureConfig.value));
    promises.push(
      setFeatureConfig.submit({ config }).catch((er) => {
        const error = `Summary settings error: ${er?.messages?.[0]}`;
        toast.error(error || "Failed to save summary settings");
      })
    );
  }

  try {
    await Promise.all(promises);
    toast.success("Otto settings updated!");
    Object.keys(isDirty.value).forEach((k) => (isDirty.value[k] = false));
  } catch {
    toast.error("Failed to save Otto settings");
  }

  isSaving.value = false;
}

function openSummarySettings() {
  currentView.value = "summary";
}

watch(
  () => hdSettings.doc,
  (newVal) =>
    (isDirty.value.hdSettings = isDocDirty(newVal, hdSettings.originalDoc)),
  { deep: true }
);
watch(
  apiKeys,
  (newVal) => {
    const keysSet = getKeysSet.data ?? {};
    isDirty.value.apiKeys = Object.keys(newVal).some((k) => {
      if (keysSet[k] && newVal[k] === dummyKey) return false;
      if (!keysSet[k] && !newVal[k]) return false;
      return true;
    });
  },
  { deep: true }
);
watch(
  featureConfig,
  (newVal) => {
    if (originalConfig.value) {
      isDirty.value.featureConfig =
        JSON.stringify(newVal) !== JSON.stringify(originalConfig.value);
    }
  },
  { deep: true }
);
</script>
