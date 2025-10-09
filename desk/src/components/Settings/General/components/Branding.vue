<template>
  <div v-if="settingsData.doc && websiteSettings.data">
    <div class="text-base font-semibold text-gray-900">Branding</div>
    <LogoUpload
      title="Logo"
      description="Appears in the left sidebar. Recommended size is 32x32 px in PNG or SVG"
      :image="settingsData.doc.brand_logo"
      @onUpload="update($event, 'HD Settings', 'brand_logo')"
      @onRemove="update('', 'HD Settings', 'brand_logo')"
      :isLoading="loadingState.logoLoading"
      :isDisabled="loadingState.faviconLoading"
    />
    <LogoUpload
      title="Favicon"
      description="Appears next to the title in your browser tab. Recommended size is 32x32 px in PNG or ICO"
      :image="websiteSettings.data.favicon"
      @onUpload="update($event, 'Website Settings', 'favicon')"
      @onRemove="update('', 'Website Settings', 'favicon')"
      :isLoading="loadingState.faviconLoading"
      :isDisabled="loadingState.logoLoading"
    />
  </div>
</template>

<script setup lang="ts">
import { inject, reactive } from "vue";
import LogoUpload from "./LogoUpload.vue";
import { createResource, toast } from "frappe-ui";

const settingsData = inject<any>("settingsData");
const loadingState = reactive({
  logoLoading: false,
  faviconLoading: false,
});

const websiteSettings = createResource({
  url: "frappe.client.get_value",
  cache: true,
  params: {
    doctype: "Website Settings",
    fieldname: "favicon",
  },
  auto: true,
});

const settingsResource = createResource({
  url: "frappe.client.set_value",
  debounce: 1000,
  onSuccess(data) {
    if (data.doctype === "HD Settings") {
      settingsData.doc.brand_logo = data.brand_logo;
      loadingState.logoLoading = false;
    } else {
      websiteSettings.data.favicon = data.favicon;
      loadingState.faviconLoading = false;
    }
    toast.success("Updated successfully");
  },
  onError() {
    loadingState.logoLoading = false;
    loadingState.faviconLoading = false;
  },
});

function update(file: string, doctype: string, fieldname: string) {
  settingsResource.submit({
    doctype: doctype,
    name: doctype,
    fieldname: fieldname,
    value: file,
  });
  doctype === "HD Settings"
    ? (loadingState.logoLoading = true)
    : (loadingState.faviconLoading = true);
}
</script>
