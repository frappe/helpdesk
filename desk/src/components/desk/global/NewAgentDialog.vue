<template>
  <div>
		<Dialog :options="{title: 'Create New Agent'}" v-model="open">
			<template #body-content>
				<div class="space-y-4">
					<div class="space-y-1">
						<Input label="Email Id" type="email" v-model="emailId" />
						<ErrorMessage :message="emailValidationError" />
					</div>
					<div class="space-y-1">
						<Input label="First Name" type="text" v-model="firstName" />
						<ErrorMessage :message="firstNameValidationError" />
					</div>
					<div class="space-y-1">
						<Input label="Last Name (optional)" type="text" v-model="lastName" />
						<ErrorMessage :message="lastNameValidationError" />
					</div>
					<div class="flex float-right space-x-2">
						<Button :loading="this.$resources.createAgent.loading" appearance="primary" @click="createAgent()">Create</Button>
					</div>
				</div>
			</template>
		</Dialog>
  </div>
</template>

<script>
import { Input, Dialog, ErrorMessage } from 'frappe-ui'
import { computed, ref, inject } from 'vue'

export default {
	name: 'NewAgentDialog',
	props: {
		modelValue: {
			type: Boolean,
			required: true,
		},
	},
	setup(props, { emit }) {
		const emailValidationError = ref('')
		const firstNameValidationError = ref('')
		const lastNameValidationError = ref('')

		const contacts = inject('contacts')

		let open = computed({
			get: () => props.modelValue,
			set: (val) => {
				emit('update:modelValue', val)
				if (!val) {
					emit('close')
				}
			},
		})

		return { open, contacts, emailValidationError, firstNameValidationError, lastNameValidationError }
	},
	data() {
		return {
			firstName: "",
			lastName: "",
			emailId: "",
		}
	},
	watch: {
		emailId(newValue) {
			this.validateEmailInput(newValue)
		},
		firstName(newValue) {
			this.validateFirstName(newValue)
		},
	},
	resources: {
		createAgent() {
			return {
				method: 'helpdesk.helpdesk.doctype.agent.agent.create_agent',
				onSuccess(data) {
					this.emailId = ''
					this.firstName = ''
					this.lastName = ''

					this.$emit('agentCreated', data)
				}
			}
		}
	},
	components: {
		Input,
		Dialog,
		ErrorMessage
	},
	methods: {
		createAgent() {
			if (this.validateInputs()) {
				return
			}

			this.$resources.createAgent.submit({
				email:this.emailId,
				first_name:this.firstName,
				last_name:this.lastName,
				signature:'',
				team:'L1' 
			})
		},
		validateInputs() {
			let error = this.validateEmailInput(this.emailId)
			error += this.validateFirstName(this.firstName)
			return error
		},
		validateEmailInput(value) {
			function existingContactEmails(contacts) {
				let list = []
				for (let index in contacts) {
					list.push(contacts[index].email_id)
				}
				return list
			}

			this.emailValidationError = ''
			const reg = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,24}))$/
			if (!value) {
				this.emailValidationError = 'Email should not be empty'
			} else if (!reg.test(value)) {
				this.emailValidationError = 'Enter a valid email'
			} else if (existingContactEmails(this.contacts).includes(value)) {
				this.emailValidationError = 'Contact with email already exists'
			}
			return this.emailValidationError
		},
		validateFirstName(value) {
			this.firstNameValidationError = ''
			if (!value) {
				this.firstNameValidationError = 'First name should not be empty'
			} else if (value.trim() == '') {
				this.firstNameValidationError = 'First name should not be empty'
			}
			return this.firstNameValidationError
		},
	}
}
</script>

<style>

</style>