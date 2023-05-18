<template>
	<div class="flex flex-col gap-2">
		{{ query }}
		<div class="text-sm text-gray-700">
			{{ help }}
		</div>
		<img v-if="imageUrl" class="m-auto h-8 w-8" :src="imageUrl" />
		<FileUploader @success="(file) => update(file)">
			<template #default="{ uploading, progress, error, openFileSelector }">
				<span>
					<Button
						class="w-max bg-gray-900 text-sm text-white hover:bg-gray-800"
						:loading="uploading"
						@click="openFileSelector"
					>
						{{ uploading ? `Uploading ${progress}%` : "Upload Image" }}
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

const query = "How about a Favicon?";
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
</script>
