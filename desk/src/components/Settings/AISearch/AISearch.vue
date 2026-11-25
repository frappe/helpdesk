<template>
  <SettingsLayoutBase
    :description="
      __(
        'Search the knowledge base by meaning, from the articles and sources each reader may see.'
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
      <div v-else class="flex flex-col gap-10">
        <section class="flex flex-col gap-2">
          <div class="flex items-center justify-between gap-8">
            <div class="flex flex-col gap-1">
              <span class="text-base-medium text-ink-gray-8">
                {{ __("Enable AI search") }}
              </span>
              <span class="text-p-sm text-ink-gray-6">
                {{
                  __(
                    "On the help center, Enter opens a page of the best matches. When off, search shows a list of matching articles."
                  )
                }}
              </span>
            </div>
            <Switch
              :model-value="enabled"
              :disabled="toggle.loading"
              @update:model-value="toggle.submit({ value: $event })"
            />
          </div>
          <span class="flex items-center gap-1.5 text-sm text-ink-gray-5">
            <LucideWorkflow class="size-3.5" />
            {{ __("Runs on Frappe Flow") }}
          </span>
        </section>

        <section class="flex flex-col gap-4">
          <div class="flex flex-col gap-1">
            <span class="text-base-semibold text-ink-gray-9">
              {{ __("Language model") }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __("Connect your own provider for the assistant.") }}
            </span>
          </div>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
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
            <div class="sm:col-span-2">
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
          </div>
        </section>

        <AISearchSources />
        <AISearchSkills />

        <section class="flex flex-col gap-4">
          <span class="text-base-semibold text-ink-gray-9">
            {{ __("Limits and guardrails") }}
          </span>
          <div class="flex items-center justify-between gap-8">
            <div class="flex flex-col gap-1">
              <span class="text-base-medium text-ink-gray-8">
                {{ __("Daily questions per visitor") }}
              </span>
              <span class="text-p-sm text-ink-gray-6">
                {{
                  __(
                    "Past the limit, search shows matching articles without AI."
                  )
                }}
              </span>
            </div>
            <FormControl
              v-model.number="draft.dailyLimit"
              type="number"
              class="w-24 shrink-0"
              :aria-label="__('Daily questions per visitor')"
            />
          </div>
          <p class="flex items-start gap-1.5 text-p-sm text-ink-gray-6">
            <LucideShieldCheck class="mt-0.5 size-3.5 shrink-0" />
            {{
              __(
                "Guardrails are always on: the assistant only helps with your product and your sources."
              )
            }}
          </p>
        </section>
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
import { computed, onUnmounted, reactive, ref, watch } from "vue";
import LucideShieldCheck from "~icons/lucide/shield-check";
import LucideWorkflow from "~icons/lucide/workflow";
import { disableSettingModalOutsideClick } from "../settingsModal";
import AISearchSkills from "./AISearchSkills.vue";
import AISearchSources from "./AISearchSources.vue";

const PROVIDERS = [
  { label: "OpenAI", value: "openai" },
  { label: "Anthropic", value: "anthropic" },
  { label: "Google Gemini", value: "gemini" },
  { label: "Mistral", value: "mistral" },
  { label: "Groq", value: "groq" },
  { label: "OpenRouter", value: "openrouter" },
];

type SaveError = { messages?: string[] };

const enabled = ref(false);
const draft = reactive({
  provider: "",
  model: "",
  apiKey: "",
  dailyLimit: 20,
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
  enabled.value = Boolean(data.enable_ai_search);
  Object.assign(draft, {
    provider: data.ai_provider || "",
    model: data.ai_model || "",
    apiKey: data.ai_api_key || "",
    dailyLimit: data.ai_daily_question_limit,
  });
  Object.assign(saved, draft);
}

function showError(error: SaveError) {
  toast.error(error.messages?.[0] || __("Could not save the settings"));
}

// The switch saves on its own; a refused change leaves it where it was.
const toggle = createResource({
  url: "frappe.client.set_value",
  makeParams: ({ value }: { value: boolean }) => ({
    doctype: "HD Settings",
    name: "HD Settings",
    fieldname: "enable_ai_search",
    value: value ? 1 : 0,
  }),
  onSuccess(data: Record<string, any>) {
    enabled.value = Boolean(data.enable_ai_search);
    toast.success(
      enabled.value ? __("AI search turned on") : __("AI search turned off")
    );
  },
  onError: showError,
});

const save = createResource({
  url: "frappe.client.set_value",
  makeParams: () => ({
    doctype: "HD Settings",
    name: "HD Settings",
    fieldname: {
      ai_provider: draft.provider,
      ai_model: draft.model,
      ai_daily_question_limit: draft.dailyLimit,
      ...(draft.apiKey !== saved.apiKey && { ai_api_key: draft.apiKey }),
    },
  }),
  onSuccess(data: Record<string, any>) {
    load(data);
    toast.success(__("Settings updated"));
  },
  onError: showError,
});

const isDirty = computed(
  () => JSON.stringify(draft) !== JSON.stringify(saved)
);

// Unsaved edits keep the modal open and guard tab changes.
watch(isDirty, (dirty) => (disableSettingModalOutsideClick.value = dirty), {
  immediate: true,
});
onUnmounted(() => (disableSettingModalOutsideClick.value = false));
</script>
