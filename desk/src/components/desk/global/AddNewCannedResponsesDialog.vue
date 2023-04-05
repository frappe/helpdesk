<template>
	<div>
		<Dialog
			:options="{ title: 'New canned response', size: '3xl' }"
			:show="show"
			@close="close()"
			class="bg-white px-6 py-5 pb-1 pt-6"
		>
			<template #body-content>
				<div class="flex flex-col mt-6">
					<Input
						id="searchInput"
						class="w-full"
						type="text"
						label="Title"
						placeholder="Enter Title"
						v-model="title"
					/>
					<ErrorMessage :message="titleValidationError" />
				</div>
				<div class="mb-2 block text-sm leading-4 text-gray-700 mt-4">
					Message
				</div>
				<div>
					<TextEditor
						class="bg-gray-100"
						ref="textEditor"
						editor-class="min-h-[20rem] overflow-y-auto max-h-[73vh] w-full px-3 max-w-full"
						:content="message"
						:starterkit-options="{
							heading: { levels: [2, 3, 4, 5, 6] },
						}"
						@change="
							(val) => {
								message = val
							}
						"
					>
						<template v-slot:top>
							<div>
								<TextEditorFixedMenu
									class="m-3 overflow-x-auto"
									:buttons="textEditorMenuButtons"
								/>
							</div>
						</template>
					</TextEditor>
				</div>
				<ErrorMessage :message="messageValidationError" />
			</template>
			<template #actions>
				<Button
					appearance="primary"
					@click="addResponse()"
					class="mr-auto"
					>Add Response</Button
				>
			</template>
		</Dialog>
	</div>
</template>

<script>
import { Dialog, Input, FeatherIcon, ErrorMessage, TextEditor } from "frappe-ui"
import { ref } from "@vue/reactivity"
import { TextEditorFixedMenu } from "frappe-ui/src/components/TextEditor"
export default {
	name: "AddNewCannedResponsesDialog",
	props: ["show"],
	components: {
		Dialog,
		Input,
		FeatherIcon,
		ErrorMessage,
		TextEditor,
		TextEditorFixedMenu,
	},
	setup() {
		const titleValidationError = ref("")
		const messageValidationError = ref("")
		return {
			titleValidationError,
			messageValidationError,
		}
	},

	data() {
		return {
			title: "",
			message: "",
		}
	},

	watch: {
		title(newValue) {
			this.validateTitle(newValue)
		},
		message(newValue) {
			this.validateMessage(newValue)
		},
	},
	computed: {
		textEditorMenuButtons() {
			return [
				"Paragraph",
				[
					"Heading 2",
					"Heading 3",
					"Heading 4",
					"Heading 5",
					"Heading 6",
				],
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
				"Video",
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
				"Undo",
				"Redo",
			]
		},
	},
	methods: {
		close() {
			this.title = ""
			this.message = ""
			this.$emit("close")
		},
		addResponse() {
			if (this.validateInputs()) {
				return
			}
			const inputParams = {
				title: this.title,
				message: this.message,
			}
			this.$resources.newResponse.submit({
				doc: {
					doctype: "HD Canned Response",
					...inputParams,
				},
			})
		},
		validateInputs() {
			let error = this.validateTitle(this.title)
			error += this.validateMessage(this.message)

			return error
		},
		validateTitle(value) {
			this.titleValidationError = ""
			if (!value) {
				this.titleValidationError = "Title is required"
			} else if (value.trim() == "") {
				this.titleValidationError = "Title is required"
			}

			return this.titleValidationError
		},

		validateMessage(value) {
			this.messageValidationError = ""
			if (!value) {
				this.messageValidationError = "Message is required"
			} else if (
				["<p><br></p>", "<p></p>"].includes(value.replaceAll(" ", ""))
			) {
				this.messageValidationError = "Message is required"
			}

			return this.messageValidationError
		},
	},
	resources: {
		newResponse() {
			return {
				url: "frappe.client.insert",
				onSuccess: (doc) => {
					this.$router.push(
						`/settings/canned_responses/${doc.name}`
					)
				},
				onError: (err) => {
					this.$toast({
						title: "Error while creating canned response",
						text: err,
						icon: "x",
						iconClasses: "text-red-500",
					})
				},
			}
		},
	},
}
</script>
