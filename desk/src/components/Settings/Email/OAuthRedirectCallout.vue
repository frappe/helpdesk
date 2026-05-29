<template>
  <div class="flex flex-col gap-3">
    <InfoAlert
      :text="intro"
      :link="serviceMeta?.link"
      :link-label="__('Read more')"
    />
    <div
      class="flex flex-col gap-2 rounded-md p-3 ring-1 ring-outline-gray-modals bg-surface-gray-1"
    >
      <div class="text-sm font-medium text-ink-gray-8">
        {{ __("Register this Redirect URI") }}
      </div>
      <div class="flex items-center gap-2">
        <code
          ref="codeElement"
          class="flex-1 truncate rounded bg-surface-gray-2 px-2 py-1.5 text-xs text-ink-gray-8 cursor-text select-all"
          :title="redirectUri || ''"
          @click="selectAll"
          >{{ redirectUri || __("Loading…") }}</code
        >
        <Button
          v-if="clipboardSupported"
          size="sm"
          variant="subtle"
          :label="copied ? __('Copied') : __('Copy')"
          :disabled="!redirectUri"
          @click="copy"
        />
      </div>
      <div v-if="whereToAdd" class="text-xs text-ink-gray-5">
        {{ whereToAdd }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { useClipboard } from "@vueuse/core";
import { Button } from "frappe-ui";
import { computed, ref } from "vue";
import InfoAlert from "./InfoAlert.vue";
import { getServiceByValue } from "../emailConfig";

interface Props {
  redirectUri: string | null;
  service?: string;
}

const props = withDefaults(defineProps<Props>(), { service: "" });

const codeElement = ref<HTMLElement | null>(null);
const {
  copy: copyToClipboard,
  copied,
  isSupported: clipboardSupported,
} = useClipboard({ legacy: true });

const serviceMeta = computed(() => getServiceByValue(props.service));

const intro = computed(() => serviceMeta.value?.info || "");

const whereToAdd = computed(() => {
  if (props.service === "GMail")
    return __(
      "Where to add it: Google Cloud Console → APIs & Services → Credentials → your OAuth 2.0 Client ID → Authorized redirect URIs."
    );
  if (props.service === "Outlook.com")
    return __(
      "Where to add it: Azure Portal → App registrations → your app → Authentication → Web → Redirect URIs."
    );
  return "";
});

function copy() {
  if (props.redirectUri) copyToClipboard(props.redirectUri);
}

function selectAll() {
  const element = codeElement.value;
  if (!element) return;
  const selection = window.getSelection();
  if (!selection) return;
  const range = document.createRange();
  range.selectNodeContents(element);
  selection.removeAllRanges();
  selection.addRange(range);
}
</script>
