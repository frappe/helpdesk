<template>
  <div>
		<Dialog :options="{title: 'Create New Agent'}" v-model="open">
			<template #body-content>
				<a href="/app/agent/new" class="text-base hover:underline text-slate-500 hover:text-slate-700"> Create Agent from frappe desk </a>
			</template>
		</Dialog>
  </div>
</template>

<script>
import { Input, Dialog } from 'frappe-ui'
import { computed } from 'vue'

export default {
	name: 'NewAgentDialog',
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
				emit('update:modelValue', val)
				if (!val) {
					emit('close')
				}
			},
		})

		return { open }
	},
	data() {
		return {
			firstName: "",
			lastName: "",
			emailId: "",
			phone: "",
		}
	},
	resources: {
		createContact() {
			return {
				method: 'frappe.client.insert',
				onSuccess(data) {
					this.$emit('contactCreated', data)
				}
			}
		}
	},
	components: {
		Input,
		Dialog,
	},
	methods: {
		createContact() {
			this.$resources.createContact.submit({
				doc: {
					doctype: 'Contact',
					first_name: this.firstName,
					last_name: this.lastName,
					email_ids: [
						{
							email_id: this.emailId
						}
					],
					phone_nos: [
						{
							phone: this.phone
						}
					]
				},
			})
		}
	}
}
</script>

<style>

</style>