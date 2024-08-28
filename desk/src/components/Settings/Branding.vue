<template>
  <div class="flex flex-col gap-4">
    <h1 class="text-lg font-semibold">Customise your Helpdesk</h1>

    <!-- Brand Logo & Favicon -->
    <div v-for="config in brandingConfig" class="flex flex-col gap-2">
      <p class="text-sm text-gray-600">{{ config.title }}</p>
      <div class="flex gap-4 items-center">
        <Avatar size="3xl" :image="config.image" />
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
            />
          </template>
        </FileUploader>
        <div v-else>
          <Button
            label="Remove"
            @click="update('', config.doctype, config.fieldname)"
            iconLeft="trash"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FileUploader, Avatar, createResource } from "frappe-ui";
import { computed, reactive } from "vue";
import { useConfigStore } from "@/stores/config";
import { createToast } from "@/utils";

const config = useConfigStore();

const state = reactive({
  brandLogo: config.brandLogo,
  brandFavicon: "",
});

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

const r = createResource({
  url: "frappe.client.set_value",
  debounce: 1000,
  onSuccess(data) {
    if (data.doctype === "HD Settings") {
      state.brandLogo = data.brand_logo;
      createToast({
        title: "Brand Logo Updated",
        icon: "check",
        iconClasses: "text-green-600",
      });
    } else {
      state.brandFavicon = data.favicon;
      createToast({
        title: "Favicon Updated",
        text: "Please refresh the page to see the changes",
        icon: "check",
        iconClasses: "text-green-600",
      });
    }
  },
  onError() {
    createToast({
      title: "Failed to update, please try again",
      icon: "x",
      iconClasses: "text-red-600",
    });
  },
});

function update(file: String, doctype: String, fieldname: String) {
  r.submit({
    doctype: doctype,
    name: doctype,
    fieldname: fieldname,
    value: file,
  });
}

const brandingConfig = computed(() => [
  {
    title: "Brand Logo",
    image: state.brandLogo,
    doctype: "HD Settings",
    fieldname: "brand_logo",
  },
  {
    title: "Brand Favicon",
    image: state.brandFavicon,
    doctype: "Website Settings",
    fieldname: "favicon",
  },
]);
</script>

<style scoped></style>
