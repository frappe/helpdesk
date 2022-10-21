<template>
	<div class="min-w-[390px] px-[24px] py-[10px]">
		<div class="form w-full flex flex-col">
			<div
				class="float-left mb-[16px]"
				@click="
					() => {
						editingName = true
						tempAgentName = values.agentName
					}
				"
			>
				<div
					v-if="!editingName"
					class="flex space-x-2 items-center cursor-pointer"
				>
					<div class="font-semibold">{{ values.agentName }}</div>
					<FeatherIcon class="w-3 h-3" name="edit-2" />
				</div>
				<div v-else class="flex space-x-2 items-center">
					<Input
						id="agentNameInput"
						v-model="tempAgentName"
						type="text"
					/>
					<FeatherIcon
						class="w-4 h-4"
						role="button"
						name="x"
						@click="
							() => {
								editingName = false
								tempAgentName = values.agentName
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
							@success="(file) => setUserImage(file.file_url)"
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
										:fullName="userDoc.full_name"
										:userImage="userDoc.user_image"
									/>
									<Button @click="openFileSelector">
										{{
											uploading
												? `Uploading ${progress}%`
												: "Upload Image"
										}}
									</Button>
									<Button
										v-if="userDoc?.user_image"
										@click="setUserImage(null)"
									>
										Remove
									</Button>
								</div>
							</template>
						</FileUploader>
					</div>
				</div>
				<div class="flex flex-row space-x-[16px]">
					<div class="grow">
						<Input
							label="Team"
							type="select"
							:options="teams"
							:value="values?.team"
							@change="(val) => (values.team = val)"
						/>
					</div>
					<!--<div class="grow">
						<Input
							label="E-mail"
							type="text"
							:value="values?.email"
							@change="(val) => (values.email = val)"
						/>
					</div> -->
				</div>
				<!-- <div class="grow">
					<Input
						label="Signature"
						type="textarea"
						:value="values?.signature"
						@change="(val) => (values.signature = val)"
					/>
				</div> -->
				<div class="w-full flex flex-row">
					<div>
						<Button @click="cancel()">Cancel</Button>
					</div>
					<div class="grow flex flex-row-reverse">
						<Button
							:loading="
								this.$resources.agent.setValue.loading ||
								this.$resources.user.setValue.loading
							"
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
	name: "AgentInfo",
	props: ["agent"],
	components: {
		FeatherIcon,
		Input,
		FileUploader,
		UserAvatar,
	},
	setup() {
		const editingName = ref(false)
		const tempAgentName = ref("")
		const updatingValues = ref(false)

		return {
			editingName,
			tempAgentName,
			updatingValues,
		}
	},
	computed: {
		agentDoc() {
			this.tempAgentName = this.$resources.agent?.doc?.agent_name
			return this.$resources.agent.doc || null
		},
		userDoc() {
			return this.$resources.user.doc || null
		},
		values() {
			if (this.updatingValues) {
				return this.values || null
			}
			return {
				agentName: this.agentDoc?.agent_name || null,
				profilePicture: this.userDoc?.user_image || null,
				team: this.agentDoc?.group || null,
				email: this.userDoc?.email || null,
				signature: this.userDoc?.email_signature || null,
			}
		},
		teams() {
			if (this.$resources.teams.data) {
				return this.$resources.teams.data.map((team) => {
					return team.name
				})
			} else {
				return []
			}
		},
	},
	deactivated() {
		this.resetForm()
	},
	resources: {
		agent() {
			return {
				type: "document",
				doctype: "Agent",
				name: this.agent,
				setValue: {
					onSuccess: () => {
						this.resetForm()
						this.updatingValues = false

						this.$toast({
							title: "Agent Updated.",
							customIcon: "circle-check",
							appearance: "success",
						})
						this.$router.go() // TODO: fix this
					},
				},
			}
		},
		user() {
			return {
				type: "document",
				doctype: "User",
				name: this.agent,
			}
		},
		teams() {
			return {
				type: "list",
				doctype: "Agent Group",
				fields: ["name"],
			}
		},
	},
	methods: {
		setUserImage(url) {
			this.$resources.user.setValue.submit({ user_image: url })
			this.$router.go() // TODO: fix this
		},
		resetForm() {
			this.editingName = false
			this.tempAgentName = this.values.agentName
		},
		save() {
			this.updatingValues = true
			const newValues = this.values

			this.$resources.user.setValue
				.submit({
					email: newValues.email,
					email_signature: newValues.signature,
					first_name: this.tempAgentName.split(" ")[0],
					last_name: this.tempAgentName.slice(
						this.tempAgentName.indexOf(" ") + 1
					),
				})
				.then(() => {
					this.$resources.agent.setValue.submit({
						agent_name: this.tempAgentName,
						group: newValues.team,
					})
				})
		},
		cancel() {
			this.$router.go()
		},
	},
}
</script>

<style></style>
