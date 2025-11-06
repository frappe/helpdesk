<template>
  <div v-if="settingsData">
    <div class="text-base font-semibold text-gray-900">
      {{ __("Branding") }}
    </div>
    <FormControl
      type="text"
      class="w-full md:w-1/2 mt-6"
      v-model="settingsData.brandName"
      :label="__('Brand name')"
      :placeholder="__('Enter brand name')"
      maxlength="30"
    />
    <LogoUpload
      :title="__('Logo')"
      :description="
        __(
          'Appears in the left sidebar. Recommended size is minimum 32x32 px in PNG or SVG'
        )
      "
      :image="brandLogo"
      @onUpload="update($event, 'HD Settings', 'brand_logo')"
      @onRemove="onRemove('HD Settings', 'brand_logo')"
      :isLoading="isLoading"
    />
    <LogoUpload
      :title="__('Favicon')"
      :description="
        __(
          'Appears next to the title in your browser tab. Recommended size is minimum 32x32 px in PNG or ICO'
        )
      "
      :image="favicon"
      @onUpload="update($event, 'HD Settings', 'favicon')"
      @onRemove="onRemove('HD Settings', 'favicon')"
      :isLoading="isLoading"
    />
  </div>
  <ConfirmDialog
    v-model="showConfirmDialog.show"
    :title="showConfirmDialog.title"
    :message="showConfirmDialog.message"
    :onConfirm="showConfirmDialog.onConfirm"
    :onCancel="() => (showConfirmDialog.show = false)"
  />
</template>

<script setup lang="ts">
import { inject, ref, watch } from "vue";
import LogoUpload from "./LogoUpload.vue";
import { createResource, toast } from "frappe-ui";
import { __ } from "@/translation";
import { useConfigStore } from "@/stores/config";
import { HDSettingsSymbol } from "@/types";

const configStore = useConfigStore();
const settingsData = inject(HDSettingsSymbol);
const isLoading = ref(false);
const brandLogo = ref(settingsData.value?.brandLogo);
const favicon = ref(settingsData.value?.favicon);

const showConfirmDialog = ref({
  show: false,
  title: "",
  message: "",
  onConfirm: () => {},
});

const settingsResource = createResource({
  url: "frappe.client.set_value",
  onSuccess(data) {
    brandLogo.value = data.brand_logo;
    favicon.value = data.favicon;
    isLoading.value = false;
    configStore.configResource.reload();
    toast.success(__("Updated successfully"));
  },
  onError() {
    isLoading.value = false;
  },
});

function update(file: string, doctype: string, fieldname: string) {
  isLoading.value = true;
  settingsResource.submit({
    doctype: doctype,
    name: doctype,
    fieldname: fieldname,
    value: file,
  });
}

const onRemove = (doctype: string, fieldname: string) => {
  showConfirmDialog.value = {
    show: true,
    title: __("Remove Logo"),
    message: __("Are you sure you want to remove the logo?"),
    onConfirm: () => {
      update("", doctype, fieldname);
      showConfirmDialog.value.show = false;
    },
  };
};

watch(settingsData, (newData) => {
  brandLogo.value = newData.brandLogo;
  favicon.value = newData.favicon;
});
</script>
