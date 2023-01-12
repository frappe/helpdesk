<template>
	<div class="min-w-[304px] px-[24px] py-[10px]">
		<div v-if="contact" class="form w-full flex flex-col">
			<div
				class="float-left mb-[16px]"
				@click="
					() => {
						editingName = true
					}
				"
			>
				<div
					v-if="!editingName"
					class="flex space-x-2 items-center cursor-pointer"
				>
					<div class="font-semibold">
						{{
							`${contact.first_name || ""} ${
								contact.last_name || ""
							}`
						}}
					</div>
					<FeatherIcon class="w-3 h-3" name="edit-2" />
				</div>
				<div v-else class="flex space-x-2">
					<div>
						<Input
							id="contactNameInput"
							:value="newContactValues.fullName"
							@change="
								(val) => {
									newContactValues.fullName = val
								}
							"
							type="text"
						/>
						<ErrorMessage :message="contactInputErrors.fullName" />
					</div>
					<FeatherIcon
						class="w-4 h-4"
						role="button"
						name="x"
						@click="
							() => {
								editingName = false
								newContactValues.fullName =
									(contact.first_name || '') +
									' ' +
									(contact.last_name || '')
							}
						"
					/>
				</div>
			</div>
			<div class="flex flex-col space-y-[24px]">
				<div>
					<span class="block mb-2 text-sm leading-4 text-gray-700"
						>Profile Picture</span
					>
					<div class="flex flex-row space-x-[8px] items-center">
						<FileUploader
							@success="(file) => setContactImage(file.file_url)"
						>
							<template
								v-slot="{
									file,
									progress,
									uploading,
									openFileSelector,
								}"
							>
								<div class="flex items-center space-x-2">
									<UserAvatar
										size="lg"
										:fullName="newContactValues?.fullName"
										:userImage="
											newContactValues?.profilePicture
										"
									/>
									<Button @click="openFileSelector">
										{{
											uploading
												? `Uploading ${progress}%`
												: "Upload Image"
										}}
									</Button>
									<Button
										v-if="newContactValues?.profilePicture"
										@click="setContactImage(null)"
									>
										Remove
									</Button>
								</div>
							</template>
						</FileUploader>
					</div>
				</div>
				<Input
					class="grow"
					label="E-mail"
					type="text"
					:value="newContactValues.email"
					@change="(val) => (newContactValues.email = val)"
				/>
				<Input
					class="grow"
					label="Phone"
					type="text"
					:value="newContactValues.phone"
					@change="(val) => (newContactValues.phone = val)"
				/>
				<div class="w-full space-y-1">
					<div>
						<span
							class="block mb-2 text-sm leading-4 text-gray-700"
						>
							Customer
						</span>
					</div>
					<Autocomplete
						:value="newContactValues.customer"
						@change="
							(item) => {
								newContactValues.customer = item.value
							}
						"
						:resourceOptions="{
							method: 'frappe.client.get_list',
							inputMap: (query) => {
								return {
									doctype: 'Helpdesk Customer',
									pluck: 'name',
									filters: [['name', 'like', `%${query}%`]],
								}
							},
							responseMap: (res) => {
								return res.map((d) => {
									return {
										label: d.name,
										value: d.name,
									}
								})
							},
						}"
					/>
					<ErrorMessage :message="contactInputErrors.customer" />
				</div>
				<div class="w-full flex flex-row">
					<div>
						<Button @click="cancel()">Cancel</Button>
					</div>
					<div class="grow flex flex-row-reverse">
						<Button
							:loading="this.$resources.contact.setValue.loading"
							appearance="primary"
							@click="
								() => {
									if (validate()) {
										save()
									}
								}
							"
							>Save</Button
						>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
<script>
import { ref } from "vue"
import { FeatherIcon, Input, FileUploader, ErrorMessage } from "frappe-ui"
import UserAvatar from "@/components/global/UserAvatar.vue"
import Autocomplete from "@/components/global/Autocomplete.vue"
export default {
	name: "ContactInfo",
	props: ["contactId"],
	components: {
		FeatherIcon,
		Input,
		FileUploader,
		UserAvatar,
		Autocomplete,
		ErrorMessage,
	},
	setup() {
		const editingName = ref(false)
		const newContactValues = ref({
			fullName: "",
			email: "",
			phone: "",
			customer: "",
			profilePicture: "",
		})
		const contactInputErrors = ref({
			fullName: "",
			email: "",
			phone: "",
			customer: "",
		})
		return {
			editingName,
			newContactValues,
			contactInputErrors,
		}
	},
	computed: {
		contact() {
			const doc = this.$resources.contact.doc
			if (doc) {
				this.newContactValues.fullName =
					(doc.first_name || "") + " " + (doc.last_name || "")
				if (doc.email_ids.length > 0) {
					this.newContactValues.email = doc.email_ids[0].email_id
				}
				if (doc.phone_nos.length > 0) {
					this.newContactValues.phone = doc.phone_nos[0].phone
				}
				if (doc.links.length > 0) {
					this.newContactValues.customer = doc.links[0].link_name
				}
				this.newContactValues.profilePicture = doc.image || ""
			}
			return doc
		},
	},
	resources: {
		contact() {
			return {
				type: "document",
				doctype: "Contact",
				name: this.contactId,
				setValue: {
					onSuccess: (res) => {
						this.$toast({
							title: "Contact Updated.",
							customIcon: "circle-check",
							appearance: "success",
						})
						this.$router.go()
					},
				},
			}
		},
	},
	methods: {
		setContactImage(url) {
			this.$resources.contact.setValue.submit({ image: url })
		},
		validate() {
			if (this.newContactValues.fullName === "") {
				this.contactInputErrors.fullName = "Name is required."
				return false
			}
			return true
		},
		save() {
			const values = this.newContactValues
			const links = []
			if (values.customer) {
				links.push({
					link_doctype: "Helpdesk Customer",
					link_name: values.customer,
				})
			}
			let firstName = ""
			let lastName = ""
			if (values.fullName.split(" ").length > 1) {
				firstName = values.fullName.split(" ")[0]
				lastName = values.fullName.substring(firstName.length + 1)
			} else {
				firstName = values.fullName
				lastName = ""
			}
			this.$resources.contact.setValue.submit({
				first_name: firstName,
				last_name: lastName,
				email_ids: values.email ? [{ email_id: values.email }] : [],
				phone_nos: values.phone ? [{ phone: values.phone }] : [],
				links,
			})
		},
		cancel() {
			this.$router.go()
		},
	},
}
</script>
