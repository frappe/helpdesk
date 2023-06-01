<template>
	<div class="px-9 py-4 text-base text-gray-700">
		<div class="flex flex-col gap-4">
			<div class="mb-4 flex items-center gap-2 text-gray-700">
				<IconHome
					class="h-4 w-4 cursor-pointer hover:text-gray-900"
					@click="goHome"
				/>
				<IconRightChevron class="h-4 w-4" />
				<RouterLink
					:to="{ name: CUSTOMER_PORTAL_LANDING }"
					class="cursor-pointer hover:text-gray-900"
				>
					My tickets
				</RouterLink>
				<IconRightChevron class="h-4 w-4" />
				New ticket
			</div>

			<div
				class="prose prose-sm max-w-full"
				v-html="sanitize(template.doc?.about)"
			/>

			<div class="grid grid-cols-3 gap-4">
				<div
					v-for="field in template.doc?.fields"
					:key="field.label"
					class="space-y-2"
				>
					<div class="text-xs">{{ field.label }}</div>
					<div v-if="field.fieldtype === 'Link'">
						<SearchComplete
							:doctype="field.options"
							@change="(v) => (customFields[field.fieldname] = v.value)"
						/>
					</div>
					<div v-else-if="field.fieldtype === 'Select'">
						<Autocomplete
							v-bind="selectOptions(field.label, field.options)"
							@change="(v) => (customFields[field.fieldname] = v.value)"
						/>
					</div>
				</div>
			</div>

			<Input v-model="subject" placeholder="Subject" />
			<TextEditor
				ref="textEditor"
				placeholder="Type a description"
				:content="description"
				:attachments="attachments"
				@change="(v) => (description = v)"
				@attachment-added="(item) => attachments.push(item)"
				@attachment-removed="(item) => removeAttachment(item)"
			>
				<template #bottom="{ editor }">
					<TextEditorBottom :editor="editor">
						<template #actions-right>
							<Button
								label="Create"
								class="bg-gray-900 text-white hover:bg-gray-800"
								:disabled="isDisabled"
								@click="create"
							/>
						</template>
					</TextEditorBottom>
				</template>
			</TextEditor>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onBeforeMount, onUnmounted, computed, reactive } from "vue";
import { useRouter } from "vue-router";
import {
	createResource,
	createDocumentResource,
	debounce,
	Autocomplete,
	Button,
	Input,
} from "frappe-ui";
import sanitizeHtml from "sanitize-html";
import { isEmpty } from "lodash";
import { CUSTOMER_PORTAL_LANDING, CUSTOMER_PORTAL_TICKET } from "@/router";
import { useConfigStore } from "@/stores/config";
import { createToast } from "@/utils/toasts";
import SearchComplete from "@/components/SearchComplete.vue";
import TextEditor from "@/components/text-editor/TextEditor.vue";
import TextEditorBottom from "@/components/text-editor/TextEditorBottom.vue";
import IconHome from "~icons/espresso/home";
import IconRightChevron from "~icons/espresso/right-chevron";

const props = defineProps({
	templateId: {
		type: String,
		required: false,
		default: "Default",
	},
});

const router = useRouter();
const configStore = useConfigStore();
const textEditor = ref();
const customFields = reactive({});

const template = createDocumentResource({
	doctype: "HD Ticket Template",
	name: props.templateId,
	fields: ["about", "fields"],
});

const subject = ref("");
const description = ref("");
const attachments = ref([]);

const r = createResource({
	url: "helpdesk.api.ticket.create_new",
	onError(error) {
		const title = error.messages?.join("\n");

		createToast({
			title,
			icon: "x",
			iconClasses: "text-red-500",
		});
	},
	onSuccess(data) {
		router.push({
			name: CUSTOMER_PORTAL_TICKET,
			params: {
				ticketId: data.name,
			},
		});
	},
});

const create = debounce(() => {
	const values = {
		subject: subject.value,
		description: description.value,
	};

	Object.assign(values, customFields);

	r.submit({
		values,
		template: props.templateId,
		attachments: attachments.value,
		via_customer_portal: true,
	});
}, 500);

const isDisabled = computed(
	() => r.loading || isEmpty(subject.value) || textEditor.value?.editor.isEmpty
);

function removeAttachment(item) {
	attachments.value = attachments.value.filter((x) => x.name != item.name);
}

function sanitize(html: string) {
	return sanitizeHtml(html, {
		allowedTags: sanitizeHtml.defaults.allowedTags.concat(["img"]),
	});
}

function goHome() {
	const protocol = window.location.protocol;
	const domain = window.location.hostname;
	const path = protocol + "//" + domain;

	window.location.href = path;
}

function selectOptions(field: string, opt: string) {
	const options = opt.split("\n").map((o) => ({
		label: o,
		value: o,
	}));
	const value = customFields[field] || [...options].shift();

	return {
		options,
		value,
	};
}

onBeforeMount(() => configStore.setTitle("New ticket"));
onUnmounted(() => configStore.setTitle());
</script>
