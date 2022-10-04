<template>
	<div>
		<Dialog :options="{ title: 'Create New Ticket' }" v-model="open">
			<template #body-content>
				<div class="space-y-4">
					<div class="w-full space-y-1">
						<div>
							<span
								class="block mb-2 text-sm leading-4 text-gray-700"
							>
								Raised By
							</span>
							<Combobox v-model="selectedContact">
								<ComboboxInput
									class="rounded-md text-base w-full py-1 border-none focus:ring-0 pl-3 pr-10 leading-5 text-gray-900 bg-gray-100"
									autocomplete="off"
									@change="query = $event.target.value"
								/>
								<ComboboxOptions
									class="absolute z-50 mt-1 overflow-auto text-base bg-white rounded-md shadow-lg max-h-40 ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm"
								>
									<div
										v-if="
											filterdContacts.length === 0 &&
											query !== ''
										"
										class="select-none py-2 relative px-4 text-slate-400"
									>
										No such contact
									</div>
									<ComboboxOption
										v-slot="{ selected, active }"
										v-for="contactItem in filterdContacts"
										:key="contactItem"
										:value="contactItem.name"
									>
										<li
											class="cursor-default select-none relative py-2 pl-4 pr-4 text-gray-900"
											:class="{ 'bg-slate-50': active }"
										>
											<span
												class="block truncate"
												:class="{
													'font-medium': selected,
													'font-normal': !selected,
												}"
											>
												{{ contactItem.name }}
											</span>
										</li>
									</ComboboxOption>
								</ComboboxOptions>
							</Combobox>
						</div>
						<ErrorMessage :message="contactValidationError" />
					</div>
					<div class="space-y-1">
						<Input label="Subject" type="text" v-model="subject" />
						<ErrorMessage :message="subjectValidationError" />
					</div>
					<div class="space-y-1">
						<div>
							<span
								class="block mb-2 text-sm leading-4 text-gray-700"
							>
								Description
							</span>
							<CustomTextEditor
								:show="true"
								:content="descriptionContent"
								editorClasses="w-full min-h-[80px] max-h-[300px] bg-gray-100 px-3 rounded-t-lg"
								@change="
									(val) => {
										descriptionContent = val
									}
								"
							>
								<template #bottom-section="{ editor }">
									<div
										class="p-1 select-none flex flex-row border-b border-x rounded-b-lg"
									>
										<div
											class="w-full flex flex-row items-center space-x-2"
										>
											<div
												v-for="item in [
													'bold',
													'italic',
													'|',
													'quote',
													'code',
													'|',
													'numbered-list',
													'bullet-list',
													'left-align',
													'center-align',
													'right-align',
												]"
												:key="item"
											>
												<TextEditorMenuItem
													:item="item"
													:editor="editor"
												/>
											</div>
										</div>
									</div>
								</template>
							</CustomTextEditor>
						</div>
						<ErrorMessage :message="descriptionValidationError" />
					</div>
					<div class="flex float-right space-x-2">
						<Button
							appearance="primary"
							@click="createTicket()"
							:loading="isCreating"
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
import { Input, Dialog, ErrorMessage } from "frappe-ui"
import CustomTextEditor from "@/components/global/CustomTextEditor.vue"
import TextEditorMenuItem from "@/components/global/TextEditorMenuItem.vue"
import { inject, ref, computed } from "vue"
import {
	Combobox,
	ComboboxInput,
	ComboboxOptions,
	ComboboxOption,
} from "@headlessui/vue"

export default {
	name: "NewTicketDialog",
	props: {
		modelValue: {
			type: Boolean,
			required: true,
		},
	},
	components: {
		CustomTextEditor,
		TextEditorMenuItem,
		Input,
		Dialog,
		ErrorMessage,
		Combobox,
		ComboboxInput,
		ComboboxOption,
		ComboboxOptions,
	},
	setup(props, { emit }) {
		const isCreating = ref(false)

		const contactName = ref("")
		const selectedContact = ref("")
		const query = ref("")

		const contacts = inject("contacts")

		const contactValidationError = ref("")
		const subjectValidationError = ref("")
		const descriptionValidationError = ref("")

		let open = computed({
			get: () => props.modelValue,
			set: (val) => {
				emit("update:modelValue", val)
				if (!val) {
					emit("close")
				}
			},
		})

		const ticketController = inject("ticketController")

		return {
			isCreating,
			contactName,
			selectedContact,
			query,
			contacts,
			contactValidationError,
			subjectValidationError,
			descriptionValidationError,
			open,
			ticketController,
		}
	},
	data() {
		return {
			subject: "",
			description: "",

			descriptionContent: "",
		}
	},
	computed: {
		filterdContacts() {
			return this.query === ""
				? this.contacts
				: this.contacts.filter((contactItem) => {
						return contactItem.name
							.toLowerCase()
							.includes(this.query.toLowerCase())
				  })
		},
	},
	watch: {
		selectedContact(newValue) {
			this.validateContactInput(newValue)
		},
		subject(newValue) {
			this.validateSubjectInput(newValue)
		},
		descriptionContent(newValue) {
			this.validateDescriptionInput(newValue)
		},
	},
	methods: {
		createTicket() {
			if (this.validateInputs()) {
				return
			}

			this.isCreating = true
			this.ticketController
				.new("ticket", {
					contact: this.selectedContact,
					subject: this.subject,
					description: this.descriptionContent,
				})
				.then(() => {
					this.isCreating = false
					this.$emit("ticketCreated")
				})
		},
		validateInputs() {
			let error = this.validateContactInput(this.selectedContact)
			error += this.validateSubjectInput(this.subject)
			error += this.validateDescriptionInput(this.descriptionContent)
			return error
		},
		validateContactInput(value) {
			this.contactValidationError = ""
			if (!value) {
				this.contactValidationError = "Contact should not be empty"
			} else if (value.trim() == "") {
				this.contactValidationError = "Contact should not be empty"
			}
			// TODO: check if the selected contact is in the list of contacts
			return this.contactValidationError
		},
		validateSubjectInput(value) {
			this.subjectValidationError = ""
			if (!value) {
				this.subjectValidationError = "Subject should not be empty"
			} else if (value.trim() == "") {
				this.subjectValidationError = "Subject should not be empty"
			} else if (value.length <= 2) {
				this.subjectValidationError =
					"Subject should be longer than that"
			}
			return this.subjectValidationError
		},
		validateDescriptionInput(value) {
			this.descriptionValidationError = ""
			if (!value) {
				this.descriptionValidationError =
					"Description should not be empty"
			} else if (
				["<p><br></p>", "<p></p>"].includes(value.replaceAll(" ", ""))
			) {
				this.descriptionValidationError =
					"Description should not be empty"
			}
			return this.subjectValidationError
		},
	},
}
</script>

<style></style>
