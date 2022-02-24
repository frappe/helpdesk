<template>
  <div>
		<Dialog :options="{title: 'Create New Agent'}" v-model="open">
			<template #body-content>
				<div class="space-y-4">
					<Input label="First Name" type="text" v-model="firstName" />
					<Input label="Last Name" type="text" v-model="lastName" />
					<Input label="Email Id" type="email" v-model="emailId" />
					<Input label="Phone" type="email" v-model="phone" />
					<div class="flex float-right space-x-2">
						<Button :loading="this.$resources.createContact.loading" appearance="primary" @click="createContact()">Create</Button>
					</div>
				</div>
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