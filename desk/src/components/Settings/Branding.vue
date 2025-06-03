<template>
  <div class="flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <h1 class="text-lg font-semibold py-[5px]">Customise your Helpdesk</h1>
    </div>

    <!-- Brand Logo & Favicon -->
    <div v-for="config in brandingConfig" class="flex flex-col gap-2">
      <p class="text-sm text-gray-600">{{ config.title }}</p>
      <div class="flex gap-4 items-center">
        <Avatar
          v-if="config.image && !config.loading"
          size="3xl"
          :image="config.image"
        />
        <FileUploader
          v-if="!config.image"
          :fileTypes="['image/*']"
          @success="
            (file) => {
              update(file.file_url, config.doctype, config.fieldname);
            }
          "
        >
          <template #default="{ openFileSelector }">
            <Button
              @click="openFileSelector()"
              iconLeft="upload"
              label="Upload Image"
              :loading="config.loading"
            />
          </template>
        </FileUploader>

        <div v-else>
          <Button
            label="Remove"
            @click="update('', config.doctype, config.fieldname)"
            iconLeft="trash"
            :loading="config.loading"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useConfigStore } from "@/stores/config";
import { Avatar, createResource, FileUploader, toast } from "frappe-ui";
import { computed, reactive } from "vue";

const config = useConfigStore();

const websiteSettings = createResource({
  url: "frappe.client.get_value",
  cache: true,
  params: {
    doctype: "Website Settings",
    fieldname: "favicon",
  },
  onSuccess(data) {
    state.brandFavicon = data.favicon;
  },
  auto: true,
});

const state = reactive({
  brandLogo: config.brandLogo,
  brandFavicon: websiteSettings.data?.favicon || "",
});

const loadingState = reactive({
  logoLoading: false,
  faviconLoading: false,
});

const brandingConfig = computed(() => [
  {
    title: "Brand Logo",
    image: state.brandLogo,
    doctype: "HD Settings",
    fieldname: "brand_logo",
    loading: loadingState.logoLoading,
  },
  {
    title: "Brand Favicon",
    image: state.brandFavicon,
    doctype: "Website Settings",
    fieldname: "favicon",
    loading: loadingState.faviconLoading,
  },
]);

const settingsResource = createResource({
  url: "frappe.client.set_value",
  debounce: 1000,
  onSuccess(data) {
    if (data.doctype === "HD Settings") {
      handleLogoChange(data.brand_logo);
    } else {
      handleFaviconChange(data.favicon);
    }
  },
  onError() {
    toast.error("Failed to update, please try again");
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

function handleLogoChange(url: string) {
  state.brandLogo = url;
  loadingState.logoLoading = false;

  toast.success("Brand logo updated");
}

function handleFaviconChange(url: string) {
  state.brandFavicon = url;
  loadingState.faviconLoading = false;
  toast.success("Favicon updated, please refresh the page to see the changes");
}
</script>

<style scoped></style>
