<template>
  <div class="flex flex-col gap-4">
    <div class="text-gray-700">
      {{ help }}
    </div>
    <img v-if="imageUrl" class="m-auto h-8 w-8" :src="imageUrl" />
    <FileUploader @success="(file) => update(file)">
      <template #default="{ error, openFileSelector }">
        <span>
          <Button
            label="Upload Favicon"
            :loading="r.loading"
            class="w-max"
            variant="outline"
            @click="openFileSelector"
          />
          <ErrorMessage class="mt-2" :message="error" />
        </span>
      </template>
    </FileUploader>
  </div>
</template>

<script setup lang="ts">
import { Ref, onMounted, ref } from "vue";
import { createResource, FileUploader } from "frappe-ui";
import { capture } from "@/telemetry";

const help =
  "A favicon enhances your website by providing a small, recognizable icon that \
	appears in browser tabs. It improves brand recognition, adds professionalism, \
	aids navigation, establishes trust, and maintains brand consistency";
const imageUrl: Ref<string> = ref(null);

const r = createResource({
  url: "frappe.client.set_value",
  debounce: 1000,
  onSuccess(data) {
    imageUrl.value = data.brand_favicon;
    capture("onboarding_favicon_changed");
  },
});

function update(file) {
  r.submit({
    doctype: "HD Settings",
    name: "HD Settings",
    fieldname: "brand_favicon",
    value: file.file_url,
  });
}

onMounted(() => capture("onboarding_favicon_reached"));
</script>
