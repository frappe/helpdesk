<template>
	<div class="p-5 overflow-auto h-full">
		<form>
			<div class="flex flex-row mb-4 w-full">
				<div class="grow flex flex-col space-y-6">
					<div class="flex flex-row w-full space-x-10">
						<div
							@click="
								() => {
									editingName = true
									if (!isNew) {
										tempEmailAccountName =
											values.emailAccountName
									}
								}
							"
							class="sm:w-6/12"
						>
							<div
								v-if="!editingName"
								class="flex space-x-2 items-center cursor-pointer"
							>
								<div class="font-semibold">
									{{ values.emailAccountName }}
								</div>
								<FeatherIcon class="w-3 h-3" name="edit" />
							</div>
							<div
								v-else
								class="flex space-x-2 max-w-sm items-center w-full"
							>
								<Input
									label="Email Account name"
									class="grow"
									id="emailAccountNameInput"
									v-model="tempEmailAccountName"
									type="text"
									placeholder="Email Account Name"
								/>
								<FeatherIcon
									v-if="!isNew"
									class="w-4 h-4 cursor-pointer"
									name="x"
									@click="
										() => {
											editingName = false
											tempEmailAccountName =
												values.emailAccountName
										}
									"
								/>
							</div>
						</div>
						<div class="sm:w-6/12"></div>
					</div>
					<div>
						<div class="flex space-x-2 items-center">
							<div class="text-base font-semibold">
								Email Setup
							</div>
						</div>
						<div class="pt-4 space-y-5 w-full">
							<div>
								<span
									class="block mb-2 text-sm leading-4 text-gray-700"
								>
									Service
								</span>
								<div
									class="flex flex-wrap text-xs text-gray-700 mx-[-4px]"
								>
									<div
										v-for="service in services"
										:key="service.title"
										role="button"
										class="h-[90px] w-[90px] m-1 p-[8px] items-center border hover:shadow-sm rounded flex flex-col space-y-2"
										:class="
											service.selected
												? 'border-2 border-blue-500 bg-blue-50'
												: 'bg-white'
										"
										@click="selectService(service)"
									>
										<Images
											:name="service.image"
											class="h-11 w-11"
										/>
										<div>{{ service.title }}</div>
									</div>
								</div>
							</div>
							<div class="flex flex-col space-y-3">
								<div
									v-if="values['service'] == 'GMail'"
									class="max-w-sm bg-blue-50 border-blue-500 rounded p-3 border-2 text-base text-gray-700 flex flex-row space-x-4 items-center"
								>
									<FeatherIcon
										name="info"
										class="shrink-0 w-6 h-6 stroke-blue-500 stroke-2"
									/>
									<p>
										GMail will only work if you enable
										2-step authentication and use
										app-specific password.
										<a
											href="https://docs.erpnext.com/docs/v13/user/manual/en/setting-up/email/email_account_setup_with_gmail"
											target="_blank"
											class="text-blue-500 hover:underline"
											>Read the step by step guide
											here.</a
										>
									</p>
								</div>
								<div
									class="max-w-sm bg-blue-50 border-blue-500 rounded p-3 border-2 text-base text-gray-700 flex flex-row space-x-4 items-center"
								>
									<FeatherIcon
										name="info"
										class="shrink-0 w-6 h-6 stroke-blue-500 stroke-2"
									/>
									<p>
										Only unseen emails will be synchronized.
									</p>
								</div>
							</div>
							<Input
								class="grow max-w-sm"
								label="Email Id"
								type="text"
								:value="values.emailId"
								placeholder="Email Id"
								@change="(val) => (values.emailId = val)"
							/>
							<Input
								@click="
									() => {
										if (!isNew) {
											if (
												initialPassword ===
												values.password
											) {
												values.password = ''
											}

											if (initialPassword === '') {
												initialPassword =
													values.password
												values.password = ''
											}
										}
									}
								"
								class="grow max-w-sm"
								label="Password"
								type="password"
								:value="values.password"
								placeholder="Password"
								@change="(val) => (values.password = val)"
							/>
						</div>
					</div>
					<div>
						<div class="flex space-x-2 items-center">
							<div class="text-base font-semibold">
								Properties
							</div>
						</div>
						<div
							class="py-4 w-full text-gray-900 text-base flex flex-col space-y-5"
						>
							<div class="flex flex-col space-y-2">
								<div
									class="flex flex-row w-full mb-2 space-x-10"
								>
									<div class="flex flex-row space-x-5">
										<div>Incoming</div>
										<CustomSwitch
											v-model="values.enableIncoming"
										/>
									</div>
									<div class="flex flex-row space-x-5">
										<div v-if="values.enableIncoming">
											Default
										</div>
										<CustomSwitch
											v-if="values.enableIncoming"
											v-model="values.defaultIncoming"
										/>
									</div>
								</div>
								<div class="flex flex-row w-full space-x-10">
									<div class="flex flex-row space-x-5">
										<div>Outgoing</div>
										<CustomSwitch
											v-model="values.enableOutgoing"
										/>
									</div>
									<div class="flex flex-row space-x-5">
										<div v-if="values.enableOutgoing">
											Default
										</div>
										<CustomSwitch
											v-if="values.enableOutgoing"
											v-model="values.defaultOutgoing"
										/>
									</div>
								</div>
							</div>
							<div
								v-if="
									!values.defaultOutgoing &&
									!values.enableOutgoing &&
									!$resources.checkDefaultOutgoingEmailAccount
										.loading &&
									$resources.checkDefaultOutgoingEmailAccount
										.data == 0
								"
								class="max-w-sm bg-yellow-50 border-yellow-500 rounded p-3 border-2 text-base text-gray-700 flex flex-row space-x-4 items-center"
							>
								<FeatherIcon
									name="alert-triangle"
									class="shrink-0 w-6 h-6 stroke-yellow-500 stroke-2"
								/>
								<p>
									There should be an email account which is
									marked as default outgoing.
								</p>
							</div>
						</div>
					</div>
				</div>
				<div>
					<div class="flex flex-row space-x-2 items-center">
						<Button appearance="secondary" @click="cancel()"
							>Cancel</Button
						>
						<Button
							appearance="primary"
							@click="
								() => {
									isNew ? create() : save()
								}
							"
							:loading="
								isNew
									? $resources.createNewEmailAccount.loading
									: $resources.updateEmailAccount.loading ||
									  $resources.renameEmailAccount.loading
							"
						>
							{{ ` ${isNew ? "Create" : "Save"}` }}
						</Button>
					</div>
				</div>
			</div>
		</form>
	</div>
</template>

<script>
import { ref } from "vue"
import CustomSwitch from "@/components/global/CustomSwitch.vue"
import Images from "@/components/global/Images.vue"
import { Input, FeatherIcon, LoadingText } from "frappe-ui"

export default {
	name: "EmailAccount",
	props: ["emailAccountId"],
	components: {
		Input,
		CustomSwitch,
		FeatherIcon,
		Images,
		LoadingText,
	},
	setup() {
		const services = ref([
			{
				title: "GMail",
				image: "gmail",
				name: "GMail",
				selected: true,
			},
			{
				title: "Outlook",
				image: "outlook",
				name: "Outlook.com",
			},
			{
				title: "Yahoo Mail",
				image: "yahoo",
				name: "Yahoo Mail",
			},
			{
				title: "Others",
				name: "Others",
			},
		])
		const emailDefaults = {
			GMail: {
				email_server: "imap.gmail.com",
				use_ssl: 1,
				smtp_server: "smtp.gmail.com",
			},
			"Outlook.com": {
				email_server: "imap-mail.outlook.com",
				use_ssl: 1,
				smtp_server: "smtp-mail.outlook.com",
			},
			Sendgrid: {
				smtp_server: "smtp.sendgrid.net",
				smtp_port: 587,
			},
			SparkPost: {
				smtp_server: "smtp.sparkpostmail.com",
			},
			"Yahoo Mail": {
				email_server: "imap.mail.yahoo.com",
				use_ssl: 1,
				smtp_server: "smtp.mail.yahoo.com",
				smtp_port: 587,
			},
			"Yandex.Mail": {
				email_server: "imap.yandex.com",
				use_ssl: 1,
				smtp_server: "smtp.yandex.com",
				smtp_port: 587,
			},
		}

		const isNew = ref(false)

		const editingName = ref(false)

		const initialPassword = ref("")

		const values = ref({
			service: services.value[0].name,
			emailAccountName: "",
			emailId: "",
			password: "",
			enableIncoming: true,
			enableOutgoing: true,
			defaultIncoming: false,
			defaultOutgoing: false,
		})

		const tempEmailAccountName = ref("")

		const errors = {
			"Error: frappe.client.set_value InvalidEmailCredentials":
				"Invalid Email ID or Password.",
			"Error: frappe.client.insert ValidationError": "Validation Error.",
			"Error: frappe.client.insert InvalidEmailCredentials":
				"Invalid Email ID or Password.",
		}

		return {
			services,
			emailDefaults,
			isNew,
			editingName,
			values,
			tempEmailAccountName,
			initialPassword,
			errors,
		}
	},
	mounted() {
		this.$event.emit("set-selected-setting", "Email Accounts")
		this.$event.emit("show-top-panel-actions-settings", "Email Account")

		this.isNew = this.$route.name === "NewEmailAccount"

		this.editingName = this.isNew

		if (this.isNew) {
			this.setDefaultValues()
		} else {
			this.$resources.getEmailAccount.fetch()
		}
	},
	methods: {
		selectService(service) {
			this.services.forEach((s) => {
				s.selected = false
			})
			service.selected = true
			this.values["service"] = service.name
		},
		setDefaultValues() {
			this.values = {
				emailAccountName: "",
				emailId: "",
				password: "",
				service: "GMail",
				enableIncoming: true,
				enableOutgoing: true,
				defaultIncoming: false,
				defaultOutgoing: false,
			}
		},
		create() {
			if (this.validateInputs()) {
				this.$resources.createNewEmailAccount.submit({
					doc: {
						doctype: "Email Account",
						email_account_name: this.tempEmailAccountName,
						email_id: this.values.emailId,
						password: this.values.password,
						enable_incoming: this.values.enableIncoming,
						enable_outgoing: this.values.enableOutgoing,
						default_incoming: this.values.defaultIncoming,
						default_outgoing: this.values.defaultOutgoing,
						email_sync_option: "UNSEEN",
						initial_sync_count: 100,
						imap_folder: [
							{
								append_to: "HD Ticket",
								folder_name: "INBOX",
							},
						],
						create_contact: true,
						track_email_status: true,
						service: this.values.service,
						use_tls: 1,
						use_imap: 1,
						smtp_port: 587,
						...this.emailDefaults[this.values.service],
					},
				})
			}
		},
		save() {
			if (this.validateInputs()) {
				this.$resources.updateEmailAccount.submit({
					doctype: "Email Account",
					name: this.values.emailAccountName,
					fieldname: {
						email_account_name: this.tempEmailAccountName,
						email_id: this.values.emailId,
						password: this.values.password,
						enable_incoming: this.values.enableIncoming,
						enable_outgoing: this.values.enableOutgoing,
						default_incoming: this.values.defaultIncoming,
						default_outgoing: this.values.defaultOutgoing,
					},
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
				new_name: this.tempEmailAccountName,
			})
		},
		validateInputs() {
			return true
		},
	},
	resources: {
		checkDefaultOutgoingEmailAccount() {
			return {
				url: "frappe.client.get_count",
				params: {
					doctype: "Email Account",
					filters: [
						["use_imap", "=", 1],
						["IMAP Folder", "append_to", "=", "HD Ticket"],
						["default_outgoing", "=", 1],
					],
				},
				onSuccess: (res) => {
					if (res == 0) {
						this.values.enableOutgoing = true
						this.values.defaultOutgoing = true
					}
				},
				auto: true,
			}
		},
		getEmailAccount() {
			return {
				url: "frappe.client.get",
				params: {
					doctype: "Email Account",
					name: this.emailAccountId,
					fields: ["*"],
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
					this.$toast({
						title: "Error getting Email Account.",
						text: this.errors[error] || error,
						icon: "x",
						iconClasses: "text-red-500",
					})
				},
			}
		},
		createNewEmailAccount() {
			return {
				url: "frappe.client.insert",
				onSuccess: () => {
					this.$toast({
						title: "Email Account Created!!",
						icon: "check",
						iconClasses: "text-green-500",
					})
					this.$clearToasts()
					this.$router.push({
						name: "Emails",
					})
				},
				onError: (error) => {
					this.$toast({
						title: "Error creating new Email Account.",
						text: this.errors[error] || error,
						icon: "x",
						iconClasses: "text-red-500",
					})
				},
			}
		},
		updateEmailAccount() {
			return {
				url: "frappe.client.set_value",
				onSuccess: () => {
					if (
						this.values.emailAccountName !=
						this.tempEmailAccountName
					) {
						this.$resources.renameEmailAccount.submit({
							doctype: "Email Account",
							old_name: this.values.emailAccountName,
							new_name: this.tempEmailAccountName,
						})
					} else {
						this.$toast({
							title: "Email Account Updated.",
							icon: "check",
							iconClasses: "text-green-500",
						})
					}
				},
				onError: (error) => {
					this.$toast({
						title: "Error updating Email Account.",
						text: this.errors[error] || error,
						icon: "x",
						iconClasses: "text-red-500",
					})
				},
			}
		},
		renameEmailAccount() {
			return {
				url: "frappe.client.rename_doc",
				onSuccess: (data) => {
					window.location.href = `/settings/emails/${data}`
				},
				onError: (error) => {
					this.$toast({
						title: "Error renaming Email Account.",
						text: this.errors[error] || error,
						icon: "x",
						iconClasses: "text-red-500",
					})
				},
			}
		},
	},
}
</script>
