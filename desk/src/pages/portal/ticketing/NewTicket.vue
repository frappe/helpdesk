<template>
	<div
		v-if="template"
		class="flex flex-row mx-auto pt-4 mt-5"
		:class="{
			'max-w-2xl': !suggestArticles,
			'max-w-5xl space-x-5': suggestArticles,
		}"
	>
		<div
			class="shrink-0"
			:class="{
				'w-[55%]': suggestArticles,
				'w-full': !suggestArticles,
			}"
		>
			<div class="rounded-lg shadow-md border p-8">
				<div class="font-medium">
					{{
						`New Ticket ${
							template.template_name != "Default"
								? `(${template.template_name})`
								: ""
						}`
					}}
				</div>
				<!-- <div v-if="template.about" class="font-normal text-base mb-3">{{ template.about }}</div> -->
				<div
					class="text-[13px] text-gray-700 pb-2"
					v-html="template.about"
				></div>
				<div class="space-y-4 pb-4">
					<div v-for="field in template.fields" :key="field">
						<div v-if="!field.auto_set">
							<div v-if="field.fieldtype == 'Data'">
								<Input
									:label="field.label"
									type="text"
									v-model="formData[field.fieldname]"
									@input="
										(data) => {
											validateField(field, data)
										}
									"
								/>
							</div>
							<div v-else-if="field.fieldtype == 'Long Text'">
								<Input
									:label="field.label"
									type="textarea"
									v-model="formData[field.fieldname]"
									@change="
										(data) => {
											validateField(field, data)
										}
									"
								/>
							</div>
							<div v-else-if="field.fieldtype == 'Text Editor'">
								<div
									class="block mb-2 text-sm leading-4 text-gray-700"
								>
									{{ field.label }}
								</div>
								<TextEditor
									:content="content"
									editor-class="px-[12px] pt-[5px] rounded-t-[8px] text-[13px] min-h-[100px] max-h-[200px] max-w-full overflow-y-scroll bg-gray-100"
									@change="
										(val) => {
											validateField(field, val)
										}
									"
									placeholder="Type your text here..."
									class="border border-gray-300 rounded-[8px]"
								>
									<template #bottom>
										<TextEditorFixedMenu
											class="bg-transparent border-t w-full px-1.5"
											:buttons="textEditorMenuButtons"
										/>
									</template>
								</TextEditor>
							</div>
							<div v-else-if="field.fieldtype == 'Link'">
								<div
									class="block mb-2 text-sm leading-4 text-gray-700"
								>
									{{ field.label }}
								</div>
								<Dropdown
									v-if="linkedFieldOptions[field.options]"
									:options="linkedFieldOptions[field.options]"
									placement="left"
									:dropdown-width-full="true"
									@change="
										(data) => {
											validateField(field, data)
										}
									"
								>
									<template v-slot="{ toggleDropdown }">
										<div>
											<Button @click="toggleDropdown">{{
												formData[field.fieldname] ||
												"Select"
											}}</Button>
										</div>
									</template>
								</Dropdown>
							</div>
							<div v-else-if="field.fieldtype == 'Select'">
								<div
									class="block mb-2 text-sm leading-4 text-gray-700"
								>
									{{ field.label }}
								</div>
								<Dropdown
									v-if="getSelectFieldOptions(field)"
									:options="getSelectFieldOptions(field)"
									placement="left"
									:dropdown-width-full="true"
									@change="
										(data) => {
											validateField(field, data)
										}
									"
								>
									<template v-slot="{ toggleDropdown }">
										<div>
											<Button @click="toggleDropdown">{{
												formData[field.fieldname] ||
												"Select"
											}}</Button>
										</div>
									</template>
								</Dropdown>
							</div>
							<ErrorMessage
								v-if="validationErrors[field.fieldname]"
								class="mt-1"
								:message="validationErrors[field.fieldname]"
							/>
						</div>
					</div>
				</div>
				<div
					class="max-h-[100px] overflow-y-scroll rounded flex flex-col"
				>
					<ul class="flex flex-wrap gap-2 pb-4">
						<li
							class="flex items-center p-1 space-x-2 bg-gray-100 border-gray-400 border shadow rounded"
							v-for="file in attachments"
							:key="file"
							:title="file.name"
						>
							<div class="flex flex-row items-center space-x-1">
								<FeatherIcon
									name="file-text"
									class="h-[15px] stroke-gray-600"
								/>
								<span
									class="text-[12px] text-gray-700 font-normal ml-2 max-w-[100px] truncate"
								>
									{{ file.file_name }}
								</span>
							</div>
							<button
								class="grid w-4 h-4 text-gray-700 rounded hover:bg-gray-300 place-items-center"
								@click="
									() => {
										attachments = attachments.filter(
											(x) => x.name != file.name
										)
									}
								"
							>
								<FeatherIcon class="w-3" name="x" />
							</button>
						</li>
					</ul>
				</div>
				<div class="flex space-x-2 mb-1">
					<FileUploader @success="(file) => attachments.push(file)">
						<template
							v-slot="{ progress, uploading, openFileSelector }"
						>
							<Button
								@click="openFileSelector"
								:disabled="uploading"
								>Add Attachment</Button
							>
						</template>
					</FileUploader>
					<div class="grow"></div>
					<Button
						:class="
							newTicketSubmitLoading
								? 'cursor-not-allowed disabled'
								: ''
						"
						@click="cancel()"
						>Cancel</Button
					>
					<Button
						:loading="newTicketSubmitLoading"
						appearance="primary"
						@click="submitTicket()"
						>Submit</Button
					>
				</div>
			</div>
		</div>
		<div v-if="suggestArticles" class="w-full px-5 border-l">
			<ArticleSuggestions :query="formData.subject || ''" />
		</div>
	</div>
</template>
<script>
import { inject, ref } from "vue"
import {
	Input,
	TextEditor,
	Card,
	Dropdown,
	ErrorMessage,
	FileUploader,
	FeatherIcon,
} from "frappe-ui"
import { call } from "frappe-ui"
import ArticleSuggestions from "@/components/global/kb/ArticleSuggestions.vue"
import { TextEditorFixedMenu } from "frappe-ui/src/components/TextEditor"

export default {
	name: "NewTicket",
	props: ["templateId"],
	components: {
		Input,
		TextEditor,
		Card,
		Dropdown,
		ErrorMessage,
		FileUploader,
		FeatherIcon,
		ArticleSuggestions,
		TextEditorFixedMenu,
	},
	setup() {
		const user = inject("user")
		const ticketTemplates = inject("ticketTemplates")
		const ticketController = inject("ticketController")

		const formData = ref({})
		const linkedFieldOptions = ref({})
		const newTicketSubmitLoading = ref(false)

		const validationErrors = ref({})

		const attachments = ref([])

		return {
			user,
			ticketTemplates,
			ticketController,
			formData,
			linkedFieldOptions,
			newTicketSubmitLoading,
			validationErrors,
			attachments,
		}
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
			]
		},
		fdSettings() {
			return this.$resources.fdSettings.doc || null
		},
		suggestArticles() {
			return this.fdSettings?.suggest_articles_in_new_ticket_page || null
		},
		template() {
			const templateRoutes = this.ticketTemplates.map(
				(x) => x.template_route
			)
			if (templateRoutes.length > 0) {
				if (!templateRoutes.includes(this.templateId)) {
					this.$router.push({ name: "DefaultNewTicket" })
					const template = this.ticketTemplates.filter(
						(x) => x.template_route == "default"
					)[0]
					this.setLinkedFieldOptions(template)
					return template
				} else {
					const template = this.ticketTemplates.filter(
						(x) => x.template_route == this.templateId
					)[0]
					this.setLinkedFieldOptions(template)
					return template
				}
			}
		},
	},
	resources: {
		fdSettings() {
			return {
				type: "document",
				doctype: "Frappe Desk Settings",
				name: "Frappe Desk Settings",
			}
		},
	},
	methods: {
		focusEditor(field) {
			const element = document.getElementsByClassName(
				`text-editor-${field.fieldname}`
			)
			element[0].getElementsByClassName("ql-editor")[0].focus()
		},
		submitTicket() {
			this.setAutoSetFields()
			if (this.validateTicketForm()) {
				this.newTicketSubmitLoading = this.ticketController.newTicket(
					this.formData,
					this.template.name,
					this.attachments.map((x) => x.name)
				)
			}
		},
		setAutoSetFields() {
			if (this.template.fields) {
				this.template.fields.forEach((field) => {
					if (
						field.auto_set &&
						field.auto_set_via === "Frontend (JS)"
					) {
						const foo = new Function(field.value_frontend)
						const value = foo()
						this.formData[field.fieldname] = value || "None"
					}
				})
			}
		},
		validateTicketForm() {
			let errors = []
			for (let index in this.template.fields) {
				let field = this.template.fields[index]
				this.validateField(
					field,
					this.formData[field.fieldname] || null
				)
				if (this.validationErrors[field.fieldname]) {
					errors.push(this.validationErrors[field.fieldname])
				}
			}
			if (errors.length > 0) {
				return false
			}
			return true
		},
		validateField(field, data) {
			let fieldname = field.fieldname
			let label = field.label

			this.validationErrors[fieldname] = null
			if (field.reqd) {
				if (!data) {
					this.validationErrors[
						fieldname
					] = `${label} is a mandatory field`
				} else if (field.fieldtype == "Text Editor") {
					if (
						["<p><br></p>", "<p></p>"].includes(
							data.replaceAll(" ", "")
						)
					) {
						this.validationErrors[
							fieldname
						] = `${label} is a mandatory field`
					}
				}
			}
			this.formData[fieldname] = data
		},
		setLinkedFieldOptions(template) {
			for (let index in template.fields) {
				let field = template.fields[index]
				if (field.fieldtype == "Link") {
					this.setLinkOptions(field)
				}
			}
		},
		getSelectFieldOptions(field) {
			let items = []
			field.options.split("\n").forEach((option) => {
				items.push({
					label: option,
					handler: () => {
						this.formData[field.fieldname] = option
					},
				})
			})
			return items
		},
		async setLinkOptions(field) {
			let doctype = field.options
			if (doctype) {
				let items = []
				let list = []
				switch (field.filter_using) {
					case "API Response":
						list = await call(field.api_method)
						break
					case "frappe.get_list()":
						list = (
							await call("frappe.client.get_list", {
								doctype,
								filters: field.filters,
							})
						).map((x) => x.name)
						break
				}
				list.forEach((doc) => {
					items.push({
						label: doc,
						handler: () => {
							this.formData[field.fieldname] = doc
						},
					})
				})
				this.linkedFieldOptions[doctype] = items
			}
			return null
		},
		cancel() {
			this.$router.push({
				name: "ProtalTickets",
			})
		},
	},
}
</script>
<style>
.ql-editor.read-mode {
	padding: 0px;
}
</style>
