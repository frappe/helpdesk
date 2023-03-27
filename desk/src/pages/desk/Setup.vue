<template>
	<div class="w-screen bg-[#F3F5F8]" style="min-height: 100vh">
		<div class="md:p-[0px] lg:p-[80px]">
			<div
				class="bg-white sm:h-[100hv] sm:rounded-none lg:rounded-[10px]"
				style="
					 {
						box-shadow: 0px 1px 42px rgba(97, 97, 97, 0.07);
						min-height: calc(100vh - 160px);
					}
				"
			>
				<div class="flex justify-center py-[60px] sm:px-[10px] lg:px-[0px]">
					<div class="flex w-[370px] flex-col space-y-[60px]">
						<div class="flex justify-center">
							<CustomIcons name="frappedesk" class="h-[24px]" />
						</div>
						<div>
							<form v-if="currentStep == 1" @submit.prevent="submitStep">
								<div class="mb-[10px] text-[24px] font-bold text-gray-900">
									Welcome to FrappeDesk
								</div>
								<div class="mb-[30px] text-[16px] font-normal text-gray-600">
									Thanks for verifying your e-mail.
								</div>
								<div class="mb-[30px] text-[16px] font-normal text-gray-900">
									Configure your e-mail address to start sending and receiving
									e-mails into FrappeDesk.
								</div>
								<div class="mb-[30px]">
									<span class="mb-2 block text-sm leading-4 text-gray-700">
										Service
									</span>
									<div
										class="mx-[-4px] flex flex-wrap text-[11px] text-gray-700"
									>
										<div
											v-for="service in services"
											:key="service.title"
											role="button"
											class="m-1 flex h-[80px] w-[80px] flex-col items-center space-y-2 rounded border p-1.5 hover:shadow-sm"
											:class="
												service.selected
													? 'border-2 border-blue-500 bg-blue-50'
													: 'bg-white'
											"
											@click="selectService(service)"
										>
											<Images :name="service.image" class="h-10 w-10" />
											<div>{{ service.title }}</div>
										</div>
									</div>
								</div>
								<div
									v-if="inputValues['service'] == 'GMail'"
									class="mb-[30px] flex flex-row items-center space-x-4 rounded border-2 border-blue-500 bg-blue-50 p-3 text-base text-gray-700"
								>
									<FeatherIcon
										name="info"
										class="h-6 w-6 shrink-0 stroke-blue-500 stroke-2"
									/>
									<p>
										GMail will only work if you enable 2-step authentication and
										use app-specific password.
										<a
											href="https://docs.erpnext.com/docs/v13/user/manual/en/setting-up/email/email_account_setup_with_gmail"
											target="_blank"
											class="text-blue-500 hover:underline"
											>Read the step by step guide here.</a
										>
									</p>
								</div>
								<label class="mb-[30px] flex flex-col space-y-[10px]">
									<span class="mb-2 block text-sm leading-4 text-gray-700">
										E-mail ID
									</span>
									<div>
										<input
											v-model="inputValues['email']"
											type="text"
											class="h-[36px] w-full rounded-[6px] border-[#EBEEF0]"
										/>
										<span
											v-if="errors['email']"
											class="text-base font-normal text-red-500"
											>{{ errors["email"] }}</span
										>
									</div>
								</label>
								<label class="mb-[30px] flex flex-col space-y-[10px]">
									<span class="mb-2 block text-sm leading-4 text-gray-700">
										Password
									</span>
									<div>
										<input
											v-model="inputValues['password']"
											type="password"
											class="h-[36px] w-full rounded-[6px] border-[#EBEEF0]"
										/>
										<span
											v-if="errors['password']"
											class="text-base font-normal text-red-500"
											>{{ errors["password"] }}</span
										>
									</div>
								</label>
								<Button appearance="primary" class="mb-[14px] w-full"
									>Next</Button
								>
								<div class="flex justify-center pl-[15px]">
									<div
										class="flex flex-row items-center space-x-3 text-center text-base font-normal text-gray-600 hover:text-gray-700"
										:class="
											$resources.completeSetup.loading
												? 'text-gray-500 hover:text-gray-500 cursor-wait'
												: 'cursor-pointer'
										"
										@click="$resources.completeSetup.submit()"
									>
										<span> Skip Onboarding </span>
										<div class="h-[15px]">
											<LoadingIndicator
												v-if="$resources.completeSetup.loading"
											/>
										</div>
									</div>
								</div>
							</form>
							<form v-if="currentStep == 2" @submit.prevent="submitStep">
								<div class="mb-[30px] text-[24px] font-bold text-gray-900">
									Let’s invite your teammates
								</div>
								<div
									v-if="emailAccountCreationSkipped"
									class="mb-[30px] flex flex-row items-center space-x-4 rounded border-2 border-yellow-300 bg-yellow-50 p-3 text-base text-gray-700"
								>
									<FeatherIcon
										name="alert-triangle"
										class="h-6 w-6 shrink-0 stroke-yellow-500 stroke-2"
									/>
									<p>
										Invitation emails will only be sent once email account is
										setup up,
										<span
											class="text-blue-500 hover:underline"
											role="button"
											@click="goBack"
											>setup up now</span
										>
									</p>
								</div>
								<label class="mb-[30px] flex flex-col space-y-[10px]">
									<span class="mb-2 block text-sm leading-4 text-gray-700">
										E-mail IDs (comma-separated)
									</span>
									<div>
										<textarea
											v-model="inputValues['agentEmailsStr']"
											rows="3"
											class="max-h-[130px] min-h-[80px] w-full rounded-[6px] border-[#EBEEF0] text-[16px] font-normal placeholder:text-gray-400"
											placeholder="tom@frappe.io, alex@frappe.io, joe@frappe.io"
										/>
										<span
											v-if="errors['agentEmailsStr']"
											class="text-base font-normal text-red-500"
											>{{ errors["agentEmailsStr"] }}</span
										>
									</div>
								</label>
								<Button
									:loading="submitInProgress"
									appearance="primary"
									class="mb-[14px] w-full"
									>Finish</Button
								>
								<div class="mb-[30px] flex justify-center">
									<div
										class="text-center text-base font-normal text-gray-600 hover:text-gray-700"
										role="button"
										@click="skip"
									>
										I’ll do this later
									</div>
								</div>
								<div
									class="max-w-fit text-base font-normal text-gray-600 hover:text-gray-700"
									role="button"
									@click="goBack"
								>
									← Back
								</div>
							</form>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import CustomIcons from "@/components/desk/global/CustomIcons.vue";
import Images from "@/components/global/Images.vue";
import { FeatherIcon, LoadingIndicator } from "frappe-ui";
import { ref } from "vue";

export default {
	name: "DeskSetup",
	components: {
		CustomIcons,
		FeatherIcon,
		Images,
		LoadingIndicator,
	},
	setup() {
		const currentStep = ref(1);
		const totalSteps = ref(2);

		const submitInProgress = ref(false);

		const emailAccountCreationSkipped = ref(true);

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
			},
			SparkPost: {
				smtp_server: "smtp.sparkpostmail.com",
			},
			"Yahoo Mail": {
				email_server: "imap.mail.yahoo.com",
				use_ssl: 1,
				smtp_server: "smtp.mail.yahoo.com",
			},
			Others: {
				use_ssl: 1,
			},
		};

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
		]);

		const inputValues = ref({
			service: services.value[0].name,
			email: "",
			password: "",
			agentEmailsStr: "",
			agentEmailList: [],
		});

		const errors = ref({});

		return {
			emailDefaults,
			submitInProgress,
			emailAccountCreationSkipped,
			currentStep,
			totalSteps,
			services,
			inputValues,
			errors,
		};
	},
	mounted() {
		this.$event.on("email-account-created", () => {
			if (this.inputValues.agentEmailList.length > 0) {
				this.$resources.sentInvites.submit({
					emails: this.inputValues.agentEmailList,
					send_welcome_mail_to_user: true,
				});
			}

			this.$resources.completeSetup.submit();
		});

		this.$event.on("email-account-creation-failed", (error) => {
			this.$toast({
				title: "Email account creation failed",
				text: error,
				icon: "x",
				iconClasses: "text-red-500",
			});

			this.submitInProgress = false;
		});
	},
	methods: {
		createEmailAccount() {
			this.submitInProgress = true;
			this.$resources.createEmailAccount.submit({
				doc: {
					doctype: "Email Account",
					email_account_name: "Support",
					email_id: this.inputValues.email,
					password: this.inputValues.password,
					enable_incoming: 1,
					enable_outgoing: 1,
					default_incoming: 0,
					default_outgoing: 1,
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
					service:
						this.inputValues.service != "Others"
							? this.inputValues.service
							: "",
					use_tls: 1,
					use_imap: 1,
					smtp_port: 587,
					...this.emailDefaults[this.inputValues.service],
				},
			});
		},
		submitStep() {
			if (this.validateInputs(this.currentStep)) {
				if (this.currentStep == 1) {
					this.emailAccountCreationSkipped = false;
				}
				if (this.currentStep < this.totalSteps) {
					this.currentStep++;
				} else {
					if (!this.emailAccountCreationSkipped) {
						this.createEmailAccount();
					} else {
						if (this.inputValues.agentEmailList.length > 0) {
							this.$resources.sentInvites
								.submit({
									emails: this.inputValues.agentEmailList,
									send_welcome_mail_to_user: false,
								})
								.then(() => {
									this.$resources.completeSetup.submit();
								});
						}
					}
				}
			}
		},
		skip() {
			if (this.currentStep == 1) {
				this.emailAccountCreationSkipped = true;
			}
			if (this.currentStep == this.totalSteps) {
				if (!this.emailAccountCreationSkipped) {
					this.createEmailAccount();
				} else {
					this.$resources.completeSetup.submit();
				}
			}
			if (this.currentStep < this.totalSteps) {
				this.currentStep++;
			}
		},
		goBack() {
			if (this.currentStep > 1) {
				this.currentStep--;
			}
		},
		selectService(service) {
			this.services.forEach((s) => {
				s.selected = false;
			});
			service.selected = true;
			this.inputValues["service"] = service.name;
		},
		validateInputs(step) {
			this.errors = {};

			const testEmailRegex = (val) => {
				let emailRegex = /^\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,3}$/;
				return emailRegex.test(val);
			};

			const textPasswordRegex = (val) => {
				let paaswordRegex = /^(?=.*\d)(?=.*[a-z]).{6,20}$/;
				return paaswordRegex.test(val);
			};

			switch (step) {
				case 1:
					// validate email
					if (!this.inputValues["email"]) {
						this.errors["email"] = "Email is required";
					} else if (!testEmailRegex(this.inputValues["email"])) {
						this.errors["email"] = "Please enter a valid email address";
					}
					// validate password
					if (!this.inputValues["password"]) {
						this.errors["password"] = "Password is required";
					} else if (!textPasswordRegex(this.inputValues["password"])) {
						this.errors["password"] =
							"Password must be at least 6 characters long and contain at least one number and one letter";
					}
					// validate service

					if (!this.inputValues["service"]) {
						this.errors["service"] = "Service is required";
					}
					break;
				case 2:
					// validate agent emails
					this.inputValues["agentEmailList"] = [];
					if (this.inputValues["agentEmailsStr"].replaceAll(" ", "") != "") {
						let agentEmailList = this.inputValues["agentEmailsStr"]
							.replaceAll(" ", "")
							.split(",");
						agentEmailList.forEach((email) => {
							if (!testEmailRegex(email)) {
								this.errors["agentEmailsStr"] =
									"Please enter a valid email address";
							}
						});
						this.inputValues["agentEmailList"] = agentEmailList;
					} else {
						this.errors["agentEmailsStr"] =
							"Please enter at least one email address";
					}
					break;
			}
			return Object.keys(this.errors).length === 0;
		},
	},
	resources: {
		createEmailAccount() {
			return {
				url: "frappe.client.insert",
				onSuccess: () => {
					this.$event.emit("email-account-created");
				},
				onError: (error) => {
					this.$event.emit("email-account-creation-failed", error);
				},
			};
		},
		sentInvites() {
			return {
				url: "frappedesk.api.agent.sent_invites",
				onSuccess: () => {
					this.$event.emit("sent-invites-success");
				},
				onError: (error) => {
					this.$event.emit("sent-invites-failed", error);
				},
			};
		},
		completeSetup() {
			return {
				url: "frappe.client.set_value",
				params: {
					doctype: "HD Settings",
					name: "HD Settings",
					fieldname: "setup_complete",
					value: 1,
				},
				onSuccess: () => {
					this.$toast({
						title: "Setup Complete",
						icon: "check",
						iconClasses: "text-green-500",
					});
					this.submitInProgress = false;
					this.$router.push({ name: "DeskTickets" });
				},
				onError: (error) => {
					this.$toast({
						title: "Setup Failed",
						text: error,
						icon: "x",
						iconClasses: "text-red-500",
					});
					this.submitInProgress = false;
				},
			};
		},
	},
};
</script>

<style scoped>
.form-input {
	background: white !important;
}
</style>
