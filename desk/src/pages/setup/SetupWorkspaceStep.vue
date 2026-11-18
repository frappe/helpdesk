<template>
  <form class="space-y-8" @submit.prevent="save">
    <div class="space-y-1.5">
      <h1 class="text-2xl-semibold text-ink-gray-9">
        {{ __("What's your company called?") }}
      </h1>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            "Customers see this name and logo on your help portal and in every reply."
          )
        }}
      </p>
    </div>

    <div class="space-y-3">
      <div class="space-y-1">
        <FormControl
          v-model="setup.brandName"
          size="lg"
          :label="__('Company or team name')"
          placeholder="Acme"
          :maxlength="BRAND_NAME_MAX_LENGTH"
          required
          autofocus
        />
        <p class="text-right text-xs tabular-nums text-ink-gray-5">
          {{ BRAND_NAME_MAX_LENGTH - setup.brandName.length }}
        </p>
      </div>

      <div class="space-y-3">
        <p class="text-sm text-ink-gray-6">{{ __("Logo") }}</p>
        <div
          ref="dropZone"
          class="flex cursor-pointer items-center gap-4 rounded-5 border border-dashed p-4 transition-colors"
          :class="
            isOverDropZone
              ? 'border-outline-gray-5 bg-surface-gray-2'
              : 'border-outline-gray-3 hover:bg-surface-gray-1'
          "
          @click="fileDialog.open()"
        >
          <span
            class="relative flex size-12 shrink-0 items-center justify-center overflow-hidden rounded-4"
            :class="
              setup.brandLogo
                ? 'ring-1 ring-outline-gray-2'
                : 'bg-surface-gray-2 text-ink-gray-5'
            "
          >
            <img
              v-if="setup.brandLogo"
              :src="setup.brandLogo"
              :alt="__('{0} logo', [brand])"
              class="size-full object-cover"
            />
            <LucideUpload v-else class="size-5" aria-hidden="true" />
            <span
              v-if="logoUpload.isUploading.value"
              class="absolute inset-0 flex items-center justify-center bg-surface-base/70"
            >
              <Spinner class="size-4 text-ink-gray-6" />
            </span>
          </span>
          <div class="min-w-0 flex-1">
            <p class="text-sm text-ink-gray-8">
              {{
                setup.brandLogo
                  ? __("Drop a new image to replace, or")
                  : __("Drop your logo here, or")
              }}
              <button
                type="button"
                class="text-ink-gray-9 underline underline-offset-2"
              >
                {{ __("browse") }}
              </button>
            </p>
            <p class="text-xs text-ink-gray-5">
              {{ __("Square, at least 128 × 128 px. PNG, JPG or SVG.") }}
            </p>
          </div>
          <Button
            v-if="setup.brandLogo"
            variant="ghost"
            size="sm"
            icon="lucide-x"
            :aria-label="__('Remove logo')"
            @click.stop="setup.brandLogo = ''"
          />
        </div>
      </div>
    </div>

    <p class="flex items-center gap-2 text-p-sm text-ink-gray-5">
      <LucideGlobe class="size-3.5" aria-hidden="true" />
      {{ __("Your help portal lives at") }}
      <span class="text-ink-gray-8">{{ portal }}</span>
    </p>

    <Transition
      enter-active-class="overflow-hidden transition-all duration-200 ease-out motion-reduce:transition-none"
      enter-from-class="!mt-0 max-h-0 opacity-0"
      enter-to-class="max-h-24"
      leave-active-class="overflow-hidden transition-all duration-150 ease-in motion-reduce:transition-none"
      leave-from-class="max-h-24"
      leave-to-class="!mt-0 max-h-0 opacity-0"
    >
      <ErrorMessage :message="saveError" />
    </Transition>

    <div class="flex justify-end">
      <Button
        type="submit"
        variant="solid"
        theme="gray"
        size="md"
        :label="__('Continue')"
        :disabled="!setup.brandName.trim()"
        :loading="saving"
      />
    </div>
  </form>
</template>

<script setup lang="ts">
import { useConfigStore } from "@/stores/config";
import { BRAND_NAME_MAX_LENGTH } from "@/utils";
import { __ } from "@/translation";
import { useDropZone, useEventListener, useFileDialog } from "@vueuse/core";
import {
  Button,
  call,
  ErrorMessage,
  FormControl,
  Spinner,
  toast,
  useFileUpload,
} from "frappe-ui";
import { ref, watch } from "vue";
import { brand, next, setup } from "./setup";

const portal = `${window.location.host}/help`;

const logoUpload = useFileUpload();
const dropZone = ref<HTMLElement | null>(null);
const { isOverDropZone } = useDropZone(dropZone, {
  onDrop: (files) => uploadLogo(files?.[0]),
  multiple: false,
});
const fileDialog = useFileDialog({
  accept: "image/*",
  multiple: false,
  reset: true,
});
fileDialog.onChange((files) => uploadLogo(files?.[0]));

async function uploadLogo(file?: File) {
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    toast.error(__("Choose an image file"));
    return;
  }
  try {
    const uploaded = await logoUpload.upload(file, { private: false });
    setup.brandLogo = uploaded.file_url;
  } catch (e) {
    toast.error(e.message || __("Could not upload the logo"));
  }
}

useEventListener(document, "paste", (event: ClipboardEvent) => {
  const file = Array.from(event.clipboardData?.files ?? []).find((f) =>
    f.type.startsWith("image/")
  );
  if (!file) return;
  event.preventDefault();
  uploadLogo(file);
});

const configStore = useConfigStore();
watch(
  () => configStore.config,
  (config) => {
    setup.brandName ||= config.brand_name || "";
    setup.brandLogo ||= config.brand_logo || "";
  },
  { immediate: true }
);

const saving = ref(false);
const saveError = ref("");

async function save() {
  if (!setup.brandName.trim() || saving.value) return;
  saving.value = true;
  saveError.value = "";
  try {
    await call("frappe.client.set_value", {
      doctype: "HD Settings",
      name: "HD Settings",
      fieldname: {
        brand_name: setup.brandName.trim(),
        brand_logo: setup.brandLogo,
      },
    });
    next();
  } catch (e) {
    saveError.value =
      e.messages?.join(" ") || __("Could not save your company");
  } finally {
    saving.value = false;
  }
}
</script>
