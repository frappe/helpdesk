<template>
	<div class="flex flex-col gap-4">
		<div class="text-gray-700">
			{{ help }}
		</div>
		<img v-if="imageUrl" class="m-auto h-8" :src="imageUrl" />
		<FileUploader @success="(file) => update(file)">
			<template #default="{ uploading, progress, error, openFileSelector }">
				<span>
					<Button
						class="w-max bg-gray-900 text-sm text-white hover:bg-gray-800"
						:loading="uploading"
						@click="openFileSelector"
					>
						{{ uploading ? `Uploading ${progress}%` : "Upload Logo" }}
					</Button>
					<ErrorMessage class="mt-2" :message="error" />
				</span>
			</template>
		</FileUploader>
	</div>
</template>

<script setup lang="ts">
import { Ref, ref } from "vue";
import { createResource, FileUploader } from "frappe-ui";

const help =
	"This will be used in many places, including Login and Loading screens. \
	An image with transparent background and a resolution of 160 x 32 is preferred";
const imageUrl: Ref<string> = ref(null);

const r = createResource({
	url: "frappe.client.set_value",
	debounce: 1000,
	onSuccess(data) {
		imageUrl.value = data.brand_logo;
	},
});

function update(file) {
	r.submit({
		doctype: "HD Settings",
		name: "HD Settings",
		fieldname: "brand_logo",
		value: file.file_url,
	});
}
</script>
