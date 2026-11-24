<template>
  <SettingsLayoutBase
    :description="
      __(
        'Give readers an answer from your knowledge base, not just a list of articles.'
      )
    "
  >
    <template #title>
      <div class="flex items-center gap-2">
        <h1 class="text-lg font-semibold text-ink-gray-8">
          {{ __("AI search") }}
        </h1>
        <UnsavedBadge :show="isDirty" />
      </div>
    </template>
    <template #header-actions>
      <Transition name="fade">
        <Button
          v-if="isDirty"
          variant="solid"
          :label="__('Save')"
          :loading="save.loading"
          @click="save.submit()"
        />
      </Transition>
    </template>
    <template #content>
      <div
        v-if="settings.loading && !settings.data"
        class="flex items-center justify-center absolute inset-x-0 top-5.5 bottom-0"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <div v-else class="flex flex-col gap-8">
        <div class="flex items-center justify-between gap-8">
          <div class="flex flex-col gap-1">
            <span class="text-base-medium text-ink-gray-8">
              {{ __("Enable AI search") }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  "On the help center, Enter opens an AI answer. When off, search shows matching articles."
                )
              }}
            </span>
          </div>
          <Switch v-model="draft.enabled" />
        </div>

        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-1">
            <span class="text-base-semibold text-ink-gray-9">
              {{ __("Language model") }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  "Connect your own provider. Answers are written with this model."
                )
              }}
            </span>
          </div>
          <FormControl
            v-model="draft.provider"
            type="select"
            :label="__('Provider')"
            :options="providerOptions"
          />
          <FormControl
            v-model="draft.model"
            :label="__('Model')"
            placeholder="gpt-4.1-mini"
          />
          <Password
            v-model="draft.apiKey"
            :label="__('API key')"
            :description="
              __(
                'Stored encrypted. Only admins can change it, and it is never shown to readers.'
              )
            "
          />
        </div>

        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              "Answers come only from the articles each reader may see. Set an embedding model in Flow Knowledge Settings so articles can be indexed."
            )
          }}
        </p>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import UnsavedBadge from "@/components/UnsavedBadge.vue";
import { __ } from "@/translation";
import {
  Button,
  createResource,
  FormControl,
  LoadingIndicator,
  Password,
  Switch,
  toast,
} from "frappe-ui";
import { computed, onUnmounted, reactive, watch } from "vue";
import { disableSettingModalOutsideClick } from "../settingsModal";

const PROVIDERS = [
  { label: "OpenAI", value: "openai" },
  { label: "Anthropic", value: "anthropic" },
  { label: "Google Gemini", value: "gemini" },
  { label: "Mistral", value: "mistral" },
  { label: "Groq", value: "groq" },
  { label: "OpenRouter", value: "openrouter" },
];

const draft = reactive({
  enabled: false,
  provider: "",
  model: "",
  apiKey: "",
});
// The saved key is masked, so a changed key is a new one.
const saved = reactive({ ...draft });

const providerOptions = computed(() =>
  PROVIDERS.some((p) => p.value === draft.provider) || !draft.provider
    ? [{ label: __("Select a provider"), value: "" }, ...PROVIDERS]
    : [{ label: draft.provider, value: draft.provider }, ...PROVIDERS]
);

const settings = createResource({
  url: "frappe.client.get",
  params: { doctype: "HD Settings", name: "HD Settings" },
  auto: true,
  onSuccess: load,
});

function load(data: Record<string, any>) {
  Object.assign(draft, {
    enabled: Boolean(data.enable_ai_search),
    provider: data.ai_provider || "",
    model: data.ai_model || "",
    apiKey: data.ai_api_key || "",
  });
  Object.assign(saved, draft);
}

const save = createResource({
  url: "frappe.client.set_value",
  makeParams: () => ({
    doctype: "HD Settings",
    name: "HD Settings",
    fieldname: {
      enable_ai_search: draft.enabled ? 1 : 0,
      ai_provider: draft.provider,
      ai_model: draft.model,
      ...(draft.apiKey !== saved.apiKey && { ai_api_key: draft.apiKey }),
    },
  }),
  onSuccess(data: Record<string, any>) {
    load(data);
    toast.success(__("Settings updated"));
  },
  onError(error: { messages?: string[] }) {
    toast.error(error.messages?.[0] || __("Could not save the settings"));
  },
});

const isDirty = computed(() => JSON.stringify(draft) !== JSON.stringify(saved));

// Unsaved edits keep the modal open and guard tab changes.
watch(isDirty, (dirty) => (disableSettingModalOutsideClick.value = dirty), {
  immediate: true,
});
onUnmounted(() => (disableSettingModalOutsideClick.value = false));
</script>
