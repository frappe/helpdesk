<template>
	<div v-if="template" class="mx-auto max-w-5xl pt-20">
		<div class="sm:w-8/12">
			<Card 
				:title="`New Ticket ${template.template_name != 'Default' ? `(${template.template_name})` : ''}`" class="space-y-6"
			>
				<div class="space-y-4 mb-4">
					<div v-for="field in template.fields" :key="field">
						<div v-if="field.fieldtype == 'Data'">
							<Input :label="field.label" type="text" v-model="formData[field.fieldname]" />
						</div>
						<div v-else-if="field.fieldtype == 'Long Text'">
							<Input :label="field.label" type="textarea" v-model="formData[field.fieldname]" />
						</div>
						<div v-else-if="field.fieldtype == 'Text Editor'">
							<div class="block mb-2 text-sm leading-4 text-gray-700">{{ field.label }}</div>
							<div>
								<TextEditor v-model="formData[field.fieldname]" showMenu="true" style="min-height:150px; max-height:200px; overflow-y: auto;" />
							</div>
						</div>
						<div v-else-if="field.fieldtype == 'Link'">
							<div class="block mb-2 text-sm leading-4 text-gray-700">{{ field.label }}</div>
							<Dropdown
								v-if="linkedFieldOptions[field.options]"
								:options="linkedFieldOptions[field.options]"
								placement="left" 
								:dropdown-width-full="true"
							>
								<template v-slot="{ toggleDropdown }">
									<div>
										<Button @click="toggleDropdown">{{ field.label }}</Button>
									</div>
								</template>
							</Dropdown>
						</div>
					</div>
				</div>
				<div>
					<Button :loading="newTicketSubmitLoading" appearance="primary" @click="submitTicket()">Submit</Button>
				</div>
				{{ formData }}
			</Card>
		</div>
	</div>
</template>
<script>
import { inject, ref } from 'vue'
import { Input, TextEditor, Card, Dropdown } from 'frappe-ui'
import { call } from 'frappe-ui'

export default {
	name: 'NewTicket',
	props: ['templateId'],
	components: {
		Input,
		TextEditor,
		Card,
		Dropdown
	},
	setup() {
		const ticketTemplates = inject('ticketTemplates')
		const ticketController = inject('ticketController')

		const formData = ref({})
		const linkedFieldOptions = ref({})
		const newTicketSubmitLoading = ref(false)

		return { ticketTemplates, ticketController, formData, linkedFieldOptions, newTicketSubmitLoading }
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
		submitTicket() {
			if (this.validateTicketForm()) {
				this.newTicketSubmitLoading = this.ticketController.newTicket(this.formData, this.template.name)
			}
		},
		validateTicketForm() {
			// TODO: check for mandatory fields
			return true
		},
		setLinkedFieldOptions(template) {
			for (let index in template.fields) {
				let field = template.fields[index]
				if (field.fieldtype == 'Link') {
					this.setLinkOptions(field)
				}
			}
		},
		async setLinkOptions(field) {
			let doctype = field.options
			if (doctype) {
				let items = [];
				let list = (await call('frappe.client.get_list', { doctype })).map(x => x.name)
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
		}
	}
}
</script>
<style>
</style>