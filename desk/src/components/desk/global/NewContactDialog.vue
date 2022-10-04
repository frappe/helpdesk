<template>
	<div>
		<Dialog :options="{ title: 'Create New Contact' }" v-model="open">
			<template #body-content>
				<div class="space-y-4">
					<div class="space-y-1">
						<Input
							label="Email Id"
							type="email"
							v-model="emailId"
						/>
						<ErrorMessage :message="emailValidationError" />
					</div>
					<div class="space-y-1">
						<Input
							label="First Name"
							type="text"
							v-model="firstName"
						/>
						<ErrorMessage :message="firstNameValidationError" />
					</div>
					<div class="space-y-1">
						<Input
							label="Last Name (optional)"
							type="text"
							v-model="lastName"
						/>
						<ErrorMessage :message="lastNameValidationError" />
					</div>
					<div class="space-y-1">
						<Input
							label="Phone (optional)"
							type="text"
							v-model="phone"
						/>
						<ErrorMessage :message="phoneValidationError" />
					</div>
					<div class="flex float-right space-x-2">
						<Button
							:loading="this.$resources.createContact.loading"
							appearance="primary"
							@click="createContact()"
							>Create</Button
						>
					</div>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script>
import { Input, Dialog, ErrorMessage } from "frappe-ui"
import { computed, ref, inject } from "vue"

export default {
	name: "NewContactDialog",
	props: {
		modelValue: {
			type: Boolean,
			required: true,
		},
	},
	setup(props, { emit }) {
		const emailValidationError = ref("")
		const firstNameValidationError = ref("")
		const lastNameValidationError = ref("")
		const phoneValidationError = ref("")

		const contacts = inject("contacts")

		let open = computed({
			get: () => props.modelValue,
			set: (val) => {
				emit("update:modelValue", val)
				if (!val) {
					emit("close")
				}
			},
		})

		return {
			open,
			contacts,
			emailValidationError,
			firstNameValidationError,
			lastNameValidationError,
			phoneValidationError,
		}
	},
	data() {
		return {
			firstName: "",
			lastName: "",
			emailId: "",
			phone: "",
		}
	},
	watch: {
		emailId(newValue) {
			this.validateEmailInput(newValue)
		},
		firstName(newValue) {
			this.validateFirstName(newValue)
		},
		phone(newValue) {
			this.validatePhone(newValue)
		},
	},
	resources: {
		createContact() {
			return {
				method: "frappe.client.insert",
				onSuccess(data) {
					this.emailId = ""
					this.firstName = ""
					this.lastName = ""
					this.phone = ""

					this.$emit("contactCreated", data)
				},
			}
		},
	},
	components: {
		Input,
		Dialog,
		ErrorMessage,
	},
	methods: {
		createContact() {
			if (this.validateInputs()) {
				return
			}

			let doc = {
				doctype: "Contact",
				first_name: this.firstName,
				last_name: this.lastName,
				email_ids: [{ email_id: this.emailId, is_primary: true }],
			}
			if (this.phone) {
				doc.phone_nos = [{ phone: this.phone }]
			}

			this.$resources.createContact.submit({
				doc,
			})
		},
		validateInputs() {
			let error = this.validateEmailInput(this.emailId)
			error += this.validateFirstName(this.firstName)
			error += this.validatePhone(this.phone)
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

			this.emailValidationError = ""
			const reg =
				/^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,24}))$/
			if (!value) {
				this.emailValidationError = "Email should not be empty"
			} else if (!reg.test(value)) {
				this.emailValidationError = "Enter a valid email"
			} else if (existingContactEmails(this.contacts).includes(value)) {
				this.emailValidationError = "Contact with email already exists"
			}
			return this.emailValidationError
		},
		validateFirstName(value) {
			this.firstNameValidationError = ""
			if (!value) {
				this.firstNameValidationError = "First name should not be empty"
			} else if (value.trim() == "") {
				this.firstNameValidationError = "First name should not be empty"
			}
			return this.firstNameValidationError
		},
		validatePhone(value) {
			this.phoneValidationError = ""
			const reg = /[0-9]+/
			if (!value) {
				this.phoneValidationError = ""
			} else if (!reg.test(value) || value.length < 10) {
				this.phoneValidationError = "Enter a valid phone number"
			}
			return this.phoneValidationError
		},
	},
}
</script>

<style></style>
