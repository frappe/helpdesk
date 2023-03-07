<template>
	<div>
		<Dialog v-model="open" :options="{ title: 'Create New Ticket' }">
			<template #body-content>
				<div class="space-y-4">
					<div class="space-y-1">
						<Input v-model="subject" label="Subject" type="text" />
						<ErrorMessage :message="subjectValidationError" />
					</div>
					<div class="w-full space-y-1">
						<div>
							<span class="mb-2 block text-sm leading-4 text-gray-700">
								Ticket Type
							</span>
						</div>
						<Autocomplete
							:value="selectedTicketType"
							:resource-options="{
								method: 'frappe.client.get_list',
								inputMap: (query) => {
									return {
										doctype: 'Ticket Type',
										pluck: 'name',
										filters: [['name', 'like', `%${query}%`]],
									};
								},
								responseMap: (res) => {
									return res.map((d) => {
										return {
											label: d.name,
											value: d.name,
										};
									});
								},
							}"
							@change="
								(item) => {
									if (!item) {
										return;
									}
									selectedTicketType = item.value;
								}
							"
						/>
					</div>
					<div class="w-full space-y-1">
						<div>
							<span class="mb-2 block text-sm leading-4 text-gray-700">
								Created By
							</span>
						</div>
						<Autocomplete
							:value="selectedContact"
							:resource-options="{
								method: 'frappe.client.get_list',
								inputMap: (query) => {
									return {
										doctype: 'Contact',
										pluck: 'name',
										filters: [['name', 'like', `%${query}%`]],
									};
								},
								responseMap: (res) => {
									return res.map((d) => {
										return {
											label: d.name,
											value: d.name,
										};
									});
								},
							}"
							@change="
								(item) => {
									if (!item) {
										return;
									}
									selectedContact = item.value;
									selectedCustomer = selectedContact.split('-')[1];
								}
							"
						/>
						<ErrorMessage :message="contactValidationError" />
					</div>
					<div class="w-full space-y-1">
						<div>
							<span class="mb-2 block text-sm leading-4 text-gray-700">
								Customer
							</span>
						</div>
						<Autocomplete
							:value="fdCustomer != null ? fdCustomer : selectedCustomer"
							:resource-options="{
								method: 'frappe.client.get_list',
								inputMap: (query) => {
									return {
										doctype: 'FD Customer',
										pluck: 'name',
										filters: [['name', 'like', `%${query}%`]],
									};
								},
								responseMap: (res) => {
									return res.map((d) => {
										return {
											label: d.name,
											value: d.name,
										};
									});
								},
							}"
							@change="
								(item) => {
									if (!item) {
										return;
									}
									selectedCustomer = item.value;
								}
							"
						/>
					</div>
					<div class="space-y-1">
						<div>
							<span class="mb-2 block text-sm leading-4 text-gray-700">
								Description
							</span>
							<TextEditor
								ref="textEditor"
								class="rounded border"
								editor-class="px-2 min-h-[8rem] overflow-y-auto max-h-[15vh]"
								:content="descriptionContent"
								:starterkit-options="{
									heading: { levels: [2, 3, 4, 5, 6] },
								}"
								:editable="true"
								@change="
									(content) => {
										descriptionContent = content;
									}
								"
							>
								<template #top>
									<TextEditorFixedMenu
										:buttons="textEditorMenuButtons"
										class="bg-gray-100"
									/>
								</template>
							</TextEditor>
						</div>
						<ErrorMessage :message="descriptionValidationError" />
					</div>
					<div class="float-right flex space-x-2">
						<Button
							appearance="primary"
							:loading="isCreating"
							@click="createTicket()"
						>
							Create
						</Button>
					</div>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script>
import { ErrorMessage, TextEditor } from "frappe-ui";
import { TextEditorFixedMenu } from "frappe-ui/src/components/TextEditor";
import Autocomplete from "@/components/global/Autocomplete.vue";
import { inject, ref, computed } from "vue";
export default {
	name: "NewTicketDialog",
	components: {
		TextEditor,
		TextEditorFixedMenu,
		Autocomplete,
		ErrorMessage,
	},
	props: {
		modelValue: {
			type: Boolean,
			required: true,
		},
		fdCustomer: {
			type: String,
			default: null,
		},
	},
	setup(props, { emit }) {
		const isCreating = ref(false);
		const selectedContact = ref("");
		const selectedTicketType = ref("");
		const contactValidationError = ref("");
		const subjectValidationError = ref("");
		const descriptionValidationError = ref("");
		const selectedCustomer = ref("");
		let open = computed({
			get: () => props.modelValue,
			set: (val) => {
				emit("update:modelValue", val);
				if (!val) {
					emit("close");
				}
			},
		});
		const ticketController = inject("ticketController");
		return {
			isCreating,
			selectedContact,
			selectedTicketType,
			contactValidationError,
			subjectValidationError,
			descriptionValidationError,
			open,
			ticketController,
			selectedCustomer,
		};
	},
	data() {
		return {
			subject: "",
			descriptionContent: "",
		};
	},
	computed: {
		textEditorMenuButtons() {
			return [
				"Paragraph",
				["Heading 2", "Heading 3", "Heading 4", "Heading 5", "Heading 6"],
				"Separator",
				"Bold",
				"Italic",
				"Separator",
				"Bullet List",
				"Numbered List",
				"Separator",
				"Align Left",
				"Align Center",
				"Align Right",
				"Separator",
				"Image",
				"Link",
				"Blockquote",
				"Code",
				"Horizontal Rule",
				[
					"InsertTable",
					"AddColumnBefore",
					"AddColumnAfter",
					"DeleteColumn",
					"AddRowBefore",
					"AddRowAfter",
					"DeleteRow",
					"MergeCells",
					"SplitCell",
					"ToggleHeaderColumn",
					"ToggleHeaderRow",
					"ToggleHeaderCell",
					"DeleteTable",
				],
				"Separator",
			];
		},
	},
	watch: {
		selectedContact(newValue) {
			this.validateContactInput(newValue);
		},
		subject(newValue) {
			this.validateSubjectInput(newValue);
		},
		descriptionContent(newValue) {
			this.validateDescriptionInput(newValue);
		},
	},
	methods: {
		createTicket() {
			if (this.validateInputs()) {
				return;
			}
			this.isCreating = true;
			this.ticketController
				.new("ticket", {
					contact: this.selectedContact,
					subject: this.subject,
					ticket_type: this.selectedTicketType,
					description: this.descriptionContent,
					customer:
						this.fdCustomer != null ? this.fdCustomer : this.selectedCustomer,
				})
				.then(() => {
					this.isCreating = false;
					this.$emit("ticket-created");
				})
				.catch(() => this.isCreating = false)
		},
		validateInputs() {
			let error = this.validateContactInput(this.selectedContact);
			error += this.validateSubjectInput(this.subject);
			error += this.validateDescriptionInput(this.descriptionContent);
			return error;
		},
		validateContactInput(value) {
			this.contactValidationError = "";
			if (!value) {
				this.contactValidationError = "Contact should not be empty";
			} else if (value.trim() == "") {
				this.contactValidationError = "Contact should not be empty";
			}
			// TODO: check if the selected contact is in the list of contacts
			return this.contactValidationError;
		},
		validateSubjectInput(value) {
			this.subjectValidationError = "";
			if (!value) {
				this.subjectValidationError = "Subject should not be empty";
			} else if (value.trim() == "") {
				this.subjectValidationError = "Subject should not be empty";
			} else if (value.length <= 2) {
				this.subjectValidationError = "Subject should be longer than that";
			}
			return this.subjectValidationError;
		},
		validateDescriptionInput(value) {
			this.descriptionValidationError = "";
			if (!value) {
				this.descriptionValidationError = "Description should not be empty";
			} else if (
				["<p><br></p>", "<p></p>"].includes(value.replaceAll(" ", ""))
			) {
				this.descriptionValidationError = "Description should not be empty";
			}
			return this.subjectValidationError;
		},
	},
};
</script>
