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
					<!-- team combobox / dropdown -->
					<div>
						<div class="block mb-2 text-sm leading-4 text-gray-700">Team</div>
						<Dropdown
							placement="left"
							:options="agentGroupsAsDropdownOptions()" 
							class="text-base w-full bg-gray-100 hover:bg-gray-200 px-2 cursor-pointer rounded mr-1"
						>
							<template v-slot="{ toggleAgentGroups }" @click="toggleAgentGroups" class="w-full">
								<div class="flex py-1 space-x-1 w-full items-center">
									<div class="grow">
										<div class="text-left">{{ team }}</div>
									</div>
								</div>
							</template>
						</Dropdown>
					</div>
					<div class="space-y-1">
						<Input label="Signature" type="textarea" v-model="signature" />
						<ErrorMessage :message="signatureValidationError" />
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
import { Input, Dialog, ErrorMessage, Dropdown } from 'frappe-ui'
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
		const signatureValidationError = ref('')
		const agentGroups = inject('agentGroups')

		const contacts = inject('contacts')	// TODO: use user instead of contacts

		let open = computed({
			get: () => props.modelValue,
			set: (val) => {
				emit('update:modelValue', val)
				if (!val) {
					emit('close')
				}
			},
		})

		return { open, contacts, emailValidationError, firstNameValidationError, lastNameValidationError, signatureValidationError, agentGroups }
	},
	data() {
		return {
			firstName: "",
			lastName: "",
			emailId: "",
			signature: "",
			team: "",
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
					this.signature = ''
					this.team = ''

					this.$emit('agentCreated', data)
				}
			}
		}
	},
	components: {
		Input,
		Dialog,
		ErrorMessage,
		Dropdown,
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
				signature:this.signature,
				team:'L1'
			})
		},
		validateInputs() {
			let error = this.validateEmailInput(this.emailId)
			error += this.validateFirstName(this.firstName)
			return error
		},
		validateEmailInput(value) {
			// function existingContactEmails(contacts) {
			// 	let list = []
			// 	for (let index in contacts) {
			// 		list.push(contacts[index].email_id)
			// 	}
			// 	return list
			// }

			this.emailValidationError = ''
			const reg = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,24}))$/
			if (!value) {
				this.emailValidationError = 'Email should not be empty'
			} else if (!reg.test(value)) {
				this.emailValidationError = 'Enter a valid email'
			} 
			// else if (existingContactEmails(this.contacts).includes(value)) {
			// 	this.emailValidationError = 'Contact with email already exists'
			// }
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
		agentGroupsAsDropdownOptions() {
			let groupItems = [];
			if (this.agentGroups) {
				this.agentGroups.forEach(group => {
					groupItems.push({
						label: group.name,
						handler: () => {
							this.team = group.name
						},
					});
				});
				if (groupItems.length == 0) {
					groupItems.push({
						label: 'No team found'
					})
				} else {
					this.team = this.agentGroups[0].name
				}
				return groupItems;
			} else {
				return null;
			}
		},
	}
}
</script>

<style>

</style>