<template>
	<div class="min-w-[304px] px-[24px] py-[10px]">
		<div class="form w-full flex flex-col">
			<div
				class="float-left mb-[16px]"
				@click="
					() => {
						editingName = true
						tempContactName = values.contactName
					}
				"
			>
				<div
					v-if="!editingName"
					class="flex space-x-2 items-center cursor-pointer"
				>
					<div class="font-semibold">{{ values.contactName }}</div>
					<FeatherIcon class="w-3 h-3" name="edit-2" />
				</div>
				<div v-else class="flex space-x-2 items-center">
					<Input
						id="contactNameInput"
						v-model="tempContactName"
						type="text"
					/>
					<FeatherIcon
						class="w-4 h-4"
						role="button"
						name="x"
						@click="
							() => {
								editingName = false
								tempContactName = values.contactName
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
										:fullName="values?.contactName"
										:userImage="values?.profilePicture"
									/>
									<Button @click="openFileSelector">
										{{
											uploading
												? `Uploading ${progress}%`
												: "Upload Image"
										}}
									</Button>
									<Button
										v-if="values?.profilePicture"
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
					:value="values?.email"
					@change="(val) => (values.email = val)"
				/>
				<Input
					class="grow"
					label="Phone"
					type="text"
					:value="values?.phone"
					@change="(val) => (values.phone = val)"
				/>
				<div class="w-full flex flex-row">
					<div>
						<Button @click="cancel()">Cancel</Button>
					</div>
					<div class="grow flex flex-row-reverse">
						<Button
							:loading="this.$resources.contact.setValue.loading"
							appearance="primary"
							@click="save()"
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
import { FeatherIcon, Input, FileUploader } from "frappe-ui"
import UserAvatar from "@/components/global/UserAvatar.vue"

export default {
	name: "ContactInfo",
	props: ["contact"],
	components: {
		FeatherIcon,
		Input,
		FileUploader,
		UserAvatar,
	},
	setup() {
		const editingName = ref(false)
		const tempContactName = ref("")

		return {
			editingName,
			tempContactName,
		}
	},
	computed: {
		contactDoc() {
			return this.$resources.contact.doc || null
		},
		values() {
			if (this.$resources.contact.setValue.loading) {
				return this.values || null
			}

			return {
				contactName: this.contactDoc
					? `${this.contactDoc?.first_name || ""} ${
							this.contactDoc?.last_name || ""
					  }`
					: "",
				profilePicture: this.contactDoc?.image || null,
				firstName: this.contactDoc?.first_name || null,
				lastName: this.contactDoc?.last_name || null,
				email:
					this.contactDoc && this.contactDoc.email_ids.length > 0
						? this.contactDoc.email_ids[0].email_id
						: "",
				phone:
					this.contactDoc && this.contactDoc.phone_nos.length > 0
						? this.contactDoc.phone_nos[0].phone
						: "",
			}
		},
	},
	deactivated() {
		this.resetForm()
	},
	resources: {
		contact() {
			return {
				type: "document",
				doctype: "Contact",
				name: this.contact,
				setValue: {
					onSuccess: () => {
						this.$toast({
							title: "Contact Updated.",
							customIcon: "circle-check",
							appearance: "success",
						})
						this.resetForm()
					},
				},
			}
		},
	},
	methods: {
		setContactImage(url) {
			this.$resources.contact.setValue.submit({ image: url })
		},
		resetForm() {
			this.editingName = false
			this.tempContactName = this.values.contactName
		},
		save() {
			let firstName = ""
			let lastName = ""
			if (this.tempContactName.split(" ").length > 1) {
				firstName = this.tempContactName.split(" ")[0]
				lastName = this.tempContactName.slice(
					firstName.length + 1,
					this.tempContactName.length
				)
			} else {
				firstName = this.tempContactName
			}

			this.$resources.contact.setValue.submit({
				first_name: firstName,
				last_name: lastName,
				email_ids: this.values.email
					? [{ email_id: this.values.email }]
					: [],
				phone_nos: this.values.phone
					? [{ phone: this.values.phone }]
					: [],
			})
		},
		cancel() {
			this.$router.go()
		},
	},
}
</script>
