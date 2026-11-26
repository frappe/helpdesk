<template>
  <div class="space-y-8">
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

    <BrandStep
      v-model:name="setup.brandName"
      v-model:logo="setup.brandLogo"
      :labels="labels"
      :max-length="BRAND_NAME_MAX_LENGTH"
      :save="save"
      @done="next()"
    >
      <template #placeholder>
        <HDLogo class="size-full" />
      </template>
      <p class="flex items-center gap-2 text-p-sm text-ink-gray-5">
        <LucideGlobe class="size-3.5" aria-hidden="true" />
        {{ __("Your help portal lives at") }}
        <span class="text-ink-gray-8">{{ portal }}</span>
      </p>
    </BrandStep>
  </div>
</template>

<script setup lang="ts">
import HDLogo from "@/assets/logos/HDLogo.vue";
import { useConfigStore } from "@/stores/config";
import { BRAND_NAME_MAX_LENGTH } from "@/utils";
import { __ } from "@/translation";
import { BrandStep } from "@framework/ui";
import { call } from "frappe-ui";
import { watch } from "vue";
import { useSetupFlow } from "./setup";

const { next, reportError, setup } = useSetupFlow();

const portal = `${window.location.host}/help`;

const labels = {
  logoLabel: __("Logo"),
  // The Helpdesk logo shows until one is uploaded, so there is always a logo to replace.
  upload: __("Replace"),
  reupload: __("Replace"),
  remove: __("Remove"),
  nameLabel: __("Company or team name"),
  namePlaceholder: "Acme",
  save: __("Continue"),
  notAnImage: __("Choose an image file"),
  uploadFailed: __("Could not upload the logo"),
  failed: __("Could not save your company"),
};

const configStore = useConfigStore();
watch(
  () => configStore.config,
  (config) => {
    setup.brandName ||= config.brand_name || "";
    setup.brandLogo ||= config.brand_logo || "";
  },
  { immediate: true }
);

async function save({ name, logo }: { name: string; logo: string }) {
  try {
    await call("frappe.client.set_value", {
      doctype: "HD Settings",
      name: "HD Settings",
      fieldname: { brand_name: name, brand_logo: logo },
    });
  } catch (e) {
    reportError("save_workspace", e);
    throw e;
  }
}
</script>
