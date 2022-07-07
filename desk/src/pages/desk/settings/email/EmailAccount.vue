<template>
	<div class="p-5 overflow-auto h-full">
		<form>
			<div class="flow-root mb-4">
				<div class="float-left" @click="() => {
					editingName = true
					tempEmailAccountName = values.emailAccountName
				}">
					<div v-if="!editingName" class="flex space-x-2 items-center cursor-pointer">
						<div class="font-semibold">{{ values.emailAccountName }}</div>
						<FeatherIcon class="w-3 h-3" name="edit-2" />
					</div>
					<div v-else class="flex space-x-2 items-center">
						<Input id="emailAccountNameInput" v-model="tempEmailAccountName" type="text" placeholder="Enter Email Account name" />
						<FeatherIcon class="w-4 h-4 cursor-pointer" name="x" @click="() => {
							editingName = false
							tempEmailAccountName = values.emailAccountName
						}" />
					</div>
				</div>
				<div class="float-right">
					<div class="flex space-x-2 items-center">
						<Button appearance="secondary" @click="cancel()">Cancel</Button>
						<Button
							appearance="primary"
							@click="() => {
								isNew ? create() : save()
							}"
							:loading="isNew ? $resources.createNewEmailAccount.loading : ($resources.updateEmailAccount.loading || $resources.renameEmailAccount.loading)"
						>
							{{ ` ${isNew ? "Create" : "Save"}` }}
						</Button>
					</div>
				</div>
			</div>
			<div class="mb-5">
				<div class="flex space-x-2 items-center">
					<div class="text-base font-semibold">Email Setup</div>
				</div>
				<div class="flex flex-row py-4 space-x-10 w-full">
					<Input class="grow max-w-sm" label="Email Id" type="text" :value="values.emailId" placeholder="Email Id" @change="(val) => values.emailId = val"/>
					<Input class="grow max-w-sm" label="Password" type="password" :value="values.password" placeholder="Password" @change="(val) => values.password = val"/>
				</div>
				<div>
					<Input class="grow max-w-sm" label="Service" type="select" :value="values.service" :options="['GMail', 'Sendgrid', 'SparkPost', 'Yahoo Mail', 'Outlook.com', 'Yandex.Mail']" @change="(val) => values.service = val" />
				</div>
			</div>
			<div class="mb-5">
				<div class="flex space-x-2 items-center">
					<div class="text-base font-semibold">Properties</div>
				</div>
				<div class="py-4 w-full text-gray-900 text-base flex flex-col space-y-2">
					<div class="flex flex-row w-full mb-2 space-x-10">
						<div class="flex flex-row space-x-5">
							<div>Incoming</div>
							<CustomSwitch v-model="values.enableIncoming" />
						</div>
						<div class="flex flex-row space-x-5">
							<div v-if="values.enableIncoming">Default</div>
							<CustomSwitch v-if="values.enableIncoming" v-model="values.defaultIncoming" />
						</div>
					</div>
					<div class="flex flex-row w-full space-x-10">
						<div class="flex flex-row space-x-5">
							<div>Outgoing</div>
							<CustomSwitch v-model="values.enableOutgoing"/>
						</div>
						<div class="flex flex-row space-x-5">
							<div v-if="values.enableOutgoing">Default</div>
							<CustomSwitch v-if="values.enableOutgoing" v-model="values.defaultOutgoing"/>
						</div>
					</div>
				</div>
			</div>
		</form>
	</div>
</template>

<script>
import { ref } from 'vue'
import CustomSwitch from '@/components/global/CustomSwitch.vue'
import { Input, FeatherIcon, LoadingText } from 'frappe-ui'

export default {
	name: "EmailAccount",
	props: ['emailAccountId'],
	components: {
		Input,
		FeatherIcon,
		CustomSwitch,
		LoadingText
	},
	setup() {
		const emailDefaults = {
			"GMail": {
				"email_server": "imap.gmail.com",
				"use_ssl": 1,
				"smtp_server": "smtp.gmail.com",
			},
			"Outlook.com": {
				"email_server": "imap-mail.outlook.com",
				"use_ssl": 1,
				"smtp_server": "smtp-mail.outlook.com",
			},
			"Sendgrid": {
				"smtp_server": "smtp.sendgrid.net",
				"smtp_port": 587
			},
			"SparkPost": {
				"smtp_server": "smtp.sparkpostmail.com",
			},
			"Yahoo Mail": {
				"email_server": "imap.mail.yahoo.com",
				"use_ssl": 1,
				"smtp_server": "smtp.mail.yahoo.com",
				"smtp_port": 587
			},
			"Yandex.Mail": {
				"email_server": "imap.yandex.com",
				"use_ssl": 1,
				"smtp_server": "smtp.yandex.com",
				"smtp_port": 587
			},
		};

		const isNew = ref(false)

		const editingName = ref(false)

		const values = ref({
			emailAccountName: '',
			emailId: '',
			password: '',
			enableIncoming: true,
			enableOutgoing: true,
			defaultIncoming: false,
			defaultOutgoing: false,
		})

		const tempEmailAccountName = ref('')

		return {
			emailDefaults,
			isNew,
			editingName,
			values,
			tempEmailAccountName
		}
	},
	activated() {
		this.$event.emit('set-selected-setting', 'Email Accounts')
		this.$event.emit('show-top-panel-actions-settings', 'Email Account')

		this.isNew = (this.$route.name === 'NewEmailAccount')

		this.editingName = false

		if (this.isNew) {
			this.setDefaultValues()
		} else {
			this.$resources.getEmailAccount.fetch()
		}
	},
	methods: {
		setDefaultValues() {
			this.values = {
				emailAccountName: 'New Email Account',
				emailId: '',
				password: '',
				service: 'GMail',
				enableIncoming: true,
				enableOutgoing: true,
				defaultIncoming: false,
				defaultOutgoing: false,
			}
		},
		create() {
			if(this.validateInputs()) {
				this.$resources.createNewEmailAccount.submit({
					doc: {
						doctype: 'Email Account',
						email_id: this.values.emailId,
						password: this.values.password,
						enable_incoming: this.values.enableIncoming,
						enable_outgoing: this.values.enableOutgoing,
						default_incoming: this.values.defaultIncoming,
						default_outgoing: this.values.defaultOutgoing,
						email_sync_option: 'UNSEEN',
						initial_sync_count: 100,
						imap_folder: [
							{
								append_to: "Ticket",
								folder_name: "INBOX",
	
							}
						],
						create_contact: true,
						track_email_status: true,
						service: this.values.service,
						use_tls: 1,
						use_imap: 1,
						smtp_port: 587,
						...this.emailDefaults[this.values.service]
					}
				})
			}
		},
		save() {
			if (this.validateInputs()) {
				this.$resources.updateEmailAccount.submit({
					doctype: 'Email Account',
					name: this.values.emailAccountName,
					fieldname: {
						email_account_name: this.tempEmailAccountName,
						email_id: this.values.emailId,
						enable_incoming: this.values.enableIncoming,
						enable_outgoing: this.values.enableOutgoing,
						default_incoming: this.values.defaultIncoming,
						default_outgoing: this.values.defaultOutgoing
					}
				})
			}
		},
		cancel() {
			this.$router.go()
		},
		rename() {
			return this.$resources.renameEmailAccount.submit({
				doctype: "Email Account",
				old_name: this.values.emailAccountName,
				new_name: this.tempEmailAccountName
			})
		},
		validateInputs() {
			return true
		}
	},
	resources: {
		getEmailAccount() {
			return {
				method: 'frappe.client.get',
				params: {
					doctype: 'Email Account',
					name: this.emailAccountId,
					fields: ['*']
				},
				onSuccess: (data) => {
					this.tempEmailAccountName = data.email_account_name
					this.values = {
						emailAccountName: data.email_account_name,
						emailId: data.email_id,
						password: data.password,
						service: data.service,
						enableIncoming: data.enable_incoming ? true : false,
						enableOutgoing: data.enable_outgoing ? true : false,
						defaultIncoming: data.default_incoming ? true : false,
						defaultOutgoing: data.default_outgoing ? true : false,
					}
				},
				onError: (error) => {
					console.log(error)
				}
			}
		},
		createNewEmailAccount() {
			return {
				method: 'frappe.client.insert',
				onSuccess: () => {
					this.$toast({
						message: 'Email Account Created',
						customIcon: 'circle-check',
						type: 'success'
					})
					this.$router.push({
						name: 'Emails'
					})
				},
				onError: (error) => {
					console.log(error)
				}
			}
		},
		updateEmailAccount() {
			return {
				method: 'frappe.client.set_value',
				onSuccess: () => {
					if (this.values.emailAccountName != this.tempEmailAccountName) {
						this.$resources.renameEmailAccount.submit({
							doctype: "Email Account",
							old_name: this.values.emailAccountName,
							new_name: this.tempEmailAccountName
						})
					} else {
						this.$toast({
							title: 'Email Account Updated.',
							customIcon: 'circle-check',
							appearance: 'success',
						})
					}
				},
				onError: (error) => {
					const errors = {
						'Error: frappe.client.set_value InvalidEmailCredentials': 'Invalid Email ID or Password.',
					}
					this.$toast({
						title: 'Error updating Email Account.',
						text: errors[error] || error,
						customIcon: 'circle-fail',
						appearance: 'danger',
					})
				}
			}
		},
		renameEmailAccount() {
			return {
				method: 'frappe.client.rename_doc',
				onSuccess: (data) => {
					window.location.href = `/frappedesk/settings/emails/${data}`
				}
			}
		}
	}
}
</script>

<style>

</style>