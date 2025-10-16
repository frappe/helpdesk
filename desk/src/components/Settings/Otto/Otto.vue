<template>
  <!-- Main Settings View -->
  <SettingsView
    v-if="currentView === 'main'"
    title="Otto"
    description="Configure Otto settings to enable smart features."
    :isDirty="isAnyDirty"
    :saving="isSaving"
    @save="save"
  >
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
    <div v-if="canUseOtto.data === true && hdSettings.doc" class="mb-6">
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
    <div
      v-if="canUseOtto.data === true && hdSettings.doc.enable_smart_features"
      class="mt-6"
    >
      <div class="text-base font-semibold text-ink-gray-8">API Keys</div>
      <div class="text-p-xs text-ink-gray-6 mt-1">
        Configure API keys for LLM providers.
      </div>
      <div class="grid grid-cols-2 gap-4 mt-4" v-if="!getKeysSet.loading">
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
      <div v-else>
        <div class="text-p-xs text-ink-gray-6 mt-1">Loading...</div>
      </div>
    </div>

    <!-- Features Section -->
    <div
      v-if="canUseOtto.data === true && hdSettings.doc?.enable_smart_features"
      class="mt-6"
    >
      <div class="text-base font-semibold text-ink-gray-8">Features</div>
      <div class="text-p-xs text-ink-gray-6 mt-1">
        Configure Otto enabled smart features.
      </div>
      <div class="mt-4">
        <!-- Summary Feature -->
        <div
          class="flex items-center justify-between p-4 border border-ink-gray-3 rounded-lg"
        >
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <h3 class="text-sm font-medium text-ink-gray-8">
                Activity Summarization
              </h3>
            </div>
            <p class="text-p-xs text-ink-gray-6 mt-1">
              Generate summary of ticket activity on demand.
            </p>
          </div>
          <div class="flex items-center gap-3">
            <Button
              label="Settings"
              theme="gray"
              variant="subtle"
              icon-left="settings"
              @click="openSummarySettings"
            />
          </div>
        </div>
      </div>
    </div>
  </SettingsView>

  <!-- Summary Settings View -->
  <SettingsView
    v-else-if="currentView === 'summary'"
    title="Activity Summarization"
    description="Configure activity summarization."
    :isDirty="isAnyDirty"
    :saving="isSaving"
    :showBackButton="true"
    @back="currentView = 'main'"
    @save="save"
  >
    <div v-if="isLoading" class="text-p-xs text-ink-gray-6">Loading...</div>
    <div v-else-if="featureConfig">
      <!-- Enable Summary Feature -->
      <div class="mb-6">
        <Checkbox
          label="Enable Activity Summarization"
          title="Summarize button will be shown if enabled."
          v-model="featureConfig.summary.enabled"
        />
        <div class="text-p-xs text-ink-gray-6 mt-1">
          Summarize button will be shown if enabled.
        </div>
      </div>

      <!-- Model Selection -->
      <div v-if="featureConfig.summary.enabled" class="mb-6">
        <FormControl
          type="select"
          label="Select a model"
          v-model="featureConfig.summary.llm"
          :options="modelOptions"
        />
        <div class="text-p-xs text-ink-gray-6 mt-1">
          LLM to use for activity summarization.
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
        <div class="text-p-xs text-ink-gray-6 mt-1">
          Guidelines such as style, format, etc to be followed during activity
          summarization.
        </div>
      </div>
    </div>
  </SettingsView>
</template>

<script setup lang="ts">
import Password from "@/components/Password.vue";
import {
  Button,
  Checkbox,
  FormControl,
  Textarea,
  createDocumentResource,
  createResource,
  toast,
} from "frappe-ui";
import { computed, ref, watch } from "vue";
import { isDocDirty } from "../Telephony/utils";
import SettingsView from "./SettingsView.vue";
import type { SmartFeatureConfig } from "./types";

type ViewType = "main" | "summary";

const currentView = ref<ViewType>("main");

const dummyKey = "••••••••••••••••••••••••••••••••";

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
const isLoading = ref(true);

const featureConfig = ref<SmartFeatureConfig>({
  summary: {
    llm: "",
    enabled: false,
    guidelines: "",
  },
});

const originalConfig = ref<SmartFeatureConfig | null>(null);
const modelOptions = ref<string[]>([]);

const canUseOtto = createResource({
  url: "helpdesk.api.otto.can_use_otto",
  auto: true,
  onSuccess: (data) => {
    if (!data) return;
    getKeysSet.reload();
    getOttoConfig.reload();
    ottoModels.reload();
  },
});

const hdSettings = createDocumentResource({
  doctype: "HD Settings",
  name: "HD Settings",
  fields: ["enable_smart_features"],
  auto: true,
});

const getKeysSet = createResource({
  url: "otto.lib.model.get_keys_set",
  onSuccess: (data) => {
    Object.keys(data).forEach((key) => {
      if (data[key]) apiKeys.value[key] = dummyKey;
    });
    isDirty.value.apiKeys = false;
  },
});

const setApiKeys = createResource({
  url: "otto.lib.model.set_api_keys",
});

const getOttoConfig = createResource({
  url: "helpdesk.api.otto.get_feature_config",
  onSuccess: (data) => {
    originalConfig.value = data;

    if (data.summary) {
      featureConfig.value.summary.llm = data.summary?.llm ?? "";
      featureConfig.value.summary.enabled = data.summary?.enabled ?? false;
      featureConfig.value.summary.guidelines = data.summary?.guidelines ?? "";
    }

    isLoading.value = false;
  },
  onError: () => {
    isLoading.value = false;
    toast.error("Failed to load summary settings");
  },
});

const ottoModels = createResource({
  url: "otto.lib.model.get_models",
  params: { get_details: true },
  onSuccess: (data) => {
    modelOptions.value = data.map((model) => ({
      label: model.title,
      value: model.name,
    }));
  },
});

const setFeatureConfig = createResource({
  url: "helpdesk.api.otto.set_feature_config",
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
    // Only send non-empty keys
    const keysToSave: Record<string, string> = {};
    if (apiKeys.value.OpenAI !== dummyKey)
      keysToSave.OpenAI = apiKeys.value.OpenAI;
    if (apiKeys.value.Anthropic !== dummyKey)
      keysToSave.Anthropic = apiKeys.value.Anthropic;
    if (apiKeys.value.Google !== dummyKey)
      keysToSave.Google = apiKeys.value.Google;

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
    isSaving.value = false;
    Object.keys(isDirty.value).forEach((key) => (isDirty.value[key] = false));

    toast.success("Otto settings updated!");
  } catch {
    toast.error("Failed to save Otto settings");
  }

  await hdSettings.reload();
}

function openSummarySettings() {
  currentView.value = "summary";
}

watch(
  () => hdSettings.doc,
  (newVal) => {
    isDirty.value.hdSettings = isDocDirty(newVal, hdSettings.originalDoc);
  },
  { deep: true }
);

watch(
  apiKeys,
  (newVal) => {
    isDirty.value.apiKeys =
      newVal.OpenAI !== dummyKey ||
      newVal.Anthropic !== dummyKey ||
      newVal.Google !== dummyKey;
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
