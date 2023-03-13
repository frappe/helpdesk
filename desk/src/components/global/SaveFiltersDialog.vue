<template>
	<Dialog
		v-model="open"
		:options="{ title: 'Save Filters' }"
		@close="reset()"
	>
		<template #body-content>
			<form class="flex flex-col space-y-5" @submit.prevent="saveFilterPreset">
				<div class="flex flex-col space-y-1">
					<Input
						type="text"
						label="Title"
						placeholder="Title of your filter preset"
						:value="titleInput"
						@input="(val) => (titleInput = val)"
					/>
					<ErrorMessage :message="titleInputError" />
				</div>
				<div class="flex items-center justify-between space-x-2 text-base">
					<div>Show to all agents</div>
					<CustomSwitch v-model="showSavedFiltersToAll" />
				</div>
			</form>
		</template>
		<template #actions>
			<Button appearance="primary" @click="saveFilterPreset">Save</Button>
		</template>
	</Dialog>
</template>

<script>
import { computed, ref } from "vue";
import CustomSwitch from "@/components/global/CustomSwitch.vue";
import { ErrorMessage } from "frappe-ui";

export default {
	name: "SaveFiltersDialog",
	components: {
		CustomSwitch,
		ErrorMessage,
	},
	inject: ["manager"],
	props: {
		modelValue: {
			type: Boolean,
			required: true,
		},
	},
	setup(props, { emit }) {
		let open = computed({
			get: () => props.modelValue,
			set: (val) => {
				emit("update:modelValue", val);
				if (!val) {
					emit("close");
				}
			},
		});

		let showSavedFiltersToAll = ref(false);
		let titleInput = ref("");
		let titleInputError = ref("");

		return {
			open,
			showSavedFiltersToAll,
			titleInput,
			titleInputError,
		};
	},
	watch: {
		titleInput(val) {
			this.validateInputs();
		},
	},
	methods: {
		saveFilterPreset() {
			if (this.validateInputs()) {
				this.$resources.saveFilterPreset.submit({
					doctype: this.manager.options.doctype,
					is_global: this.showSavedFiltersToAll,
					title: this.titleInput,
					filters: this.manager.sudoFilters,
				});
			}
		},
		validateInputs() {
			this.titleInputError = "";
			if (this.titleInput === "") {
				this.titleInputError = "Title is required";
				return false;
			}
			return true;
		},
		close() {
			this.open = false;
			this.reset();
		},
		reset() {
			this.showSavedFiltersToAll = false;
			this.titleInput = "";
			this.titleInputError = "";
		},
	},
	resources: {
		saveFilterPreset() {
			return {
				url: "frappedesk.api.general.save_filter_preset",
				onSuccess: (res) => {
					this.$toast({
						title: "Filter Saved!",
						icon: "check",
						iconClasses: "text-green-500",
					});

					this.close();
				},
				onError: (err) => {
					this.$toast({
						title: "Error Sending Invites!",
						text: err,
						icon: "x",
						iconClasses: "text-red-500",
					});

					this.close();
				},
			};
		},
	},
};
</script>
