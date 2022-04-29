<template>
	<div v-if="template" class="mx-auto max-w-2xl pt-4">
		<div>
			<div class="rounded-lg shadow-md border p-8">
				<div class="font-medium mb-3">{{ `New Ticket ${template.template_name != 'Default' ? `(${template.template_name})` : ''}` }}</div>
				<div v-if="template.about" class="font-normal text-base mb-3">{{ template.about }}</div>
				<div class="space-y-4 mb-4">
					<div v-for="field in template.fields" :key="field">
						<div v-if="!field.auto_set">
							<div v-if="field.fieldtype == 'Data'">
								<Input :label="field.label" type="text" v-model="formData[field.fieldname]" @change="(data) => {validateField(field, data)}"/>
							</div>
							<div v-else-if="field.fieldtype == 'Long Text'">
								<Input :label="field.label" type="textarea" v-model="formData[field.fieldname]" @change="(data) => {validateField(field, data)}"/>
							</div>
							<div v-else-if="field.fieldtype == 'Text Editor'">
								<div class="block mb-2 text-sm leading-4 text-gray-700">{{ field.label }}</div>
								<div>
									<quill-editor  
										content=""
										contentType="html" 
										:options="editorOptions"
										style="min-height:150px; max-height:200px; overflow-y: auto;"
										@update:content="(data) => {validateField(field, data)}"
										@click="focusEditor(field)"
										:class="`text-editor-${field.fieldname}`"
									/>
								</div>
							</div>
							<div v-else-if="field.fieldtype == 'Link'">
								<div class="block mb-2 text-sm leading-4 text-gray-700">{{ field.label }}</div>
								<Dropdown
									v-if="linkedFieldOptions[field.options]"
									:options="linkedFieldOptions[field.options]"
									placement="left" 
									:dropdown-width-full="true"
									@change="(data) => {validateField(field, data)}"
								>
									<template v-slot="{ toggleDropdown }">
										<div>
											<Button @click="toggleDropdown">{{ formData[field.fieldname] || `Select ${field.label}` }}</Button>
										</div>
									</template>
								</Dropdown>
							</div>
							<div v-else-if="field.fieldtype == 'Select'">
								<div class="block mb-2 text-sm leading-4 text-gray-700">{{ field.label }}</div>
								<Dropdown
									v-if="getSelectFieldOptions(field)"
									:options="getSelectFieldOptions(field)"
									placement="left" 
									:dropdown-width-full="true"
									@change="(data) => {validateField(field, data)}"
								>
									<template v-slot="{ toggleDropdown }">
										<div>
											<Button @click="toggleDropdown">{{ formData[field.fieldname] || `Select ${field.label}` }}</Button>
										</div>
									</template>
								</Dropdown>
							</div>
							<ErrorMessage v-if="validationErrors[field.fieldname]" class="mt-1" :message="validationErrors[field.fieldname]" />
						</div>
					</div>
				</div>
				<div class="flex space-x-2 mb-1">
					<div class="grow"></div>
					<Button :class="newTicketSubmitLoading ? 'cursor-not-allowed disabled' : ''" @click="cancel()">Cancel</Button>
					<Button :loading="newTicketSubmitLoading" appearance="primary" @click="submitTicket()">Submit</Button>
				</div>
			</div>
			<!-- <Card 
				:title="`New Ticket ${template.template_name != 'Default' ? `(${template.template_name})` : ''}`" class="space-y-6"
			>
				
			</Card> -->
		</div>
	</div>
</template>
<script>
import { inject, ref } from 'vue'
import { Input, TextEditor, Card, Dropdown, ErrorMessage } from 'frappe-ui'
import { call } from 'frappe-ui'
import '@vueup/vue-quill/dist/vue-quill.snow.css';
import { QuillEditor } from '@vueup/vue-quill'

export default {
	name: 'NewTicket',
	props: ['templateId'],
	components: {
		Input,
		TextEditor,
		Card,
		Dropdown,
		ErrorMessage,
		QuillEditor
	},
	setup() {
		const user = inject('user')
		const ticketTemplates = inject('ticketTemplates')
		const ticketController = inject('ticketController')

		const formData = ref({})
		const linkedFieldOptions = ref({})
		const newTicketSubmitLoading = ref(false)

		const validationErrors = ref({})

		const editorOptions = ref({
			modules: {
				toolbar: [
					['bold', 'italic', 'underline', 'strike'],        // toggled buttons
					['blockquote', 'code-block'],

					[{ 'header': 1 }, { 'header': 2 }],               // custom button values
					[{ 'list': 'ordered'}, { 'list': 'bullet' }],

					[{ 'header': [1, 2, 3, 4, 5, 6, false] }],

					[{ 'color': [] }, { 'background': [] }],          // dropdown with defaults from theme
					
					['image'],
					
					[{ 'align': [] }],

					['clean']                                         // remove formatting button
				]
			},
			placeholder: 'Compose your reply...',
			theme: 'snow',
			bounds: 7,
		})

		return { user, ticketTemplates, ticketController, formData, linkedFieldOptions, newTicketSubmitLoading, validationErrors, editorOptions }
	},
	computed: {
		template() {
			const templateRoutes = this.ticketTemplates.map(x => x.template_route)
			if (templateRoutes.length > 0) {
				if (!templateRoutes.includes(this.templateId)) {
					this.$router.push({ name: "DefaultNewTicket" })
					const template = this.ticketTemplates.filter(x => x.template_route == 'default')[0]
					this.setLinkedFieldOptions(template)
					return template
				} else {
					const template = this.ticketTemplates.filter(x => x.template_route == this.templateId)[0]
					this.setLinkedFieldOptions(template)
					return template
				}
			}
		}
	},
	resources: {

	},
	methods: {
		focusEditor(field) {
			const element = document.getElementsByClassName(`text-editor-${field.fieldname}`)
			element[0].getElementsByClassName("ql-editor")[0].focus()
		},
		submitTicket() {
			if (this.validateTicketForm()) {
				this.newTicketSubmitLoading = this.ticketController.newTicket(this.formData, this.template.name)
			}
		},
		validateTicketForm() {
			let errors = []
			for (let index in this.template.fields) {
				let field = this.template.fields[index]
				this.validateField(field, this.formData[field.fieldname] || null)
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
					this.validationErrors[fieldname] = `${label} is a mandatory field`
				} else if (field.fieldtype == 'Text Editor') {
					if (['<p><br></p>', '<p></p>'].includes(data.replaceAll(' ', ''))) {
						this.validationErrors[fieldname] = `${label} is a mandatory field`
					}
				}
			}
			if (!this.validationErrors[fieldname]) {
				this.formData[fieldname] = data
			}
		},
		setLinkedFieldOptions(template) {
			for (let index in template.fields) {
				let field = template.fields[index]
				if (field.fieldtype == 'Link') {
					this.setLinkOptions(field)
				}
			}
		},
		getSelectFieldOptions(field) {
			let items = []
			field.options.split('\n').forEach((option) => {
				items.push({
					label: option,
					handler: () => {
						this.formData[field.fieldname] = option
					}
				})
			})
			return items
		},
		async setLinkOptions(field) {
			let doctype = field.options
			if (doctype) {
				let items = [];
				let list = []
				switch(field.filter_using) {
					case 'API Response':
						list = await call(field.api_method)
						break;
					case 'frappe.get_list()':
						list = [...new Set((await call('frappe.client.get_list', { doctype, filters: field.filters, fields: [field.pluck] })).map(x => x[field.pluck]))]
						console.log(list)
						break;
				}
				list.forEach(doc => {
					items.push({
						label: doc,
						handler: () => {
							this.formData[field.fieldname] = doc
						},
					});
				});
				this.linkedFieldOptions[doctype] = items
			}
			return null
		},
		cancel() {
			this.$router.push({
				name: 'ProtalTickets',
			})
		}
	}
}
</script>
<style>
</style>