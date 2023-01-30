<template>
	<div class="min-w-[490px] px-6 py-2.5">
		<div class="shrink-0 h-[72px] py-5 flow-root px-4">
			<div class="float-left">
				<router-link
					:to="`/frappedesk/settings/teams`"
					class="my-1 text-sm text-gray-600 stroke-gray-600 flex flex-row items-center space-x-1 hover:text-gray-700 hover:stroke-gray-700 select-none"
					role="button"
				>
					<FeatherIcon name="arrow-left" class="w-3 h-3" />
					<div>Back to team list</div>
				</router-link>
			</div>
			<div class="float-right">
				<div class="flex flex-row space-x-2">
					<Button appearance="secondary" @click="cancel">
						Cancel
					</Button>
					<Button
						appearance="primary"
						@click="
							() => {
								if (validate()) {
									save()
								}
							}
						"
					>
						Save
					</Button>
				</div>
			</div>
		</div>
		<div
			v-if="team"
			class="flex flex-row space-x-[24px] h-full border-t px-4 py-5"
		>
			<div class="flex flex-col space-y-[16px] h-full w-full">
				<div>
					<Input
						label="Title"
						type="text"
						:value="team.name"
						@input="
							(val) => {
								newTeamValues['title'] = val
							}
						"
					/>
					<ErrorMessage :message="teamInputErrors['title']" />
				</div>
				<form
					@submit.prevent="onSubmit"
					class="flex flex-row space-x-2 items-end"
				>
					<div class="w-full space-y-1">
						<div>
							<span class="block text-sm leading-4 text-gray-700">
								Users
							</span>
						</div>
						<Autocomplete
							id="searchInput"
							:value="''"
							@change="
								(item) => {
									if (
										!newTeamValues.users.includes(
											item.value
										)
									) {
										newTeamValues.users.push(item.value)
									}
								}
							"
							:resourceOptions="{
								method: 'frappe.client.get_list',
								inputMap: (query) => {
									return {
										doctype: 'Agent',
										fields: ['name', 'agent_name'],
										filters: {
											name: ['like', `%${query}%`],
										},
									}
								},
								responseMap: (res) => {
									return res.map((d) => {
										return {
											label: d.agent_name,
											value: d.name,
										}
									})
								},
							}"
						/>
					</div>
				</form>
				<div
					class="bg-gray-100 min-h-[100px] max-h-[300px] overflow-y-auto px-2 rounded border flex flex-col"
				>
					<ul
						v-if="newTeamValues.users.length > 0"
						class="flex flex-wrap gap-2 py-2"
					>
						<li
							v-for="user in newTeamValues.users"
							class="flex items-center p-1 space-x-2 bg-white shadow rounded"
							:key="user"
						>
							<span class="text-base ml-2">
								{{ user }}
							</span>
							<button
								class="grid w-4 h-4 text-gray-700 rounded hover:bg-gray-300 place-items-center"
								@click="
									() => {
										newTeamValues.users =
											newTeamValues.users.filter(
												(u) => u !== user
											)
									}
								"
							>
								<FeatherIcon class="w-3" name="x" />
							</button>
						</li>
					</ul>
				</div>
			</div>
		</div>
	</div>
</template>
<script>
import { ref } from "vue"
import { FeatherIcon, ErrorMessage } from "frappe-ui"
import Autocomplete from "@/components/global/Autocomplete.vue"
export default {
	name: "TeamInfo",
	props: ["teamId"],
	components: {
		FeatherIcon,
		Autocomplete,
		ErrorMessage,
	},
	setup() {
		const newTeamValues = ref({
			title: "",
			users: [],
		})
		const teamInputErrors = ref({
			title: "",
		})
		return {
			newTeamValues,
			teamInputErrors,
		}
	},
	computed: {
		team() {
			if (this.teamId) {
				const doc = this.$resources.team.doc
				if (doc) {
					this.newTeamValues["title"] = doc.name
					let users = []
					doc.users.map((res) => {
						users.push(res["user"])
					})
					this.newTeamValues["users"] = users
				}
				return doc
			} else {
				return { title: "", users: [] }
			}
		},
	},
	resources: {
		team() {
			if (!this.teamId) return
			return {
				type: "document",
				doctype: "Agent Group",
				fields: ["name", "users"],
				name: this.teamId,
				setValue: {
					onSuccess: () => {
						this.$toast({
							title: "Team Updated.",
							customIcon: "circle-check",
							appearance: "success",
						})
					},
					onError: (err) => {
						this.$toast({
							title: "Error while updating ticket type",
							text: err,
							customIcon: "circle-fail",
							appearance: "danger",
						})
					},
				},
			}
		},
		renameTeamDoc() {
			return {
				method: "frappe.client.rename_doc",
				onSuccess: (res) => {
					this.$router.push({
						path: `/frappedesk/settings/teams/${res}`,
					})
				},
			}
		},
		newTeam() {
			return {
				method: "frappe.client.insert",
				onSuccess: (res) => {
					this.$router.push({
						path: `/frappedesk/settings/teams/${res.name}`,
					})
				},
			}
		},
	},
	methods: {
		validate() {
			if (this.newTeamValues.title === "") {
				this.teamInputErrors.title = "Team name is required"
				return false
			} else if (this.newTeamValues.title === "new") {
				this.teamInputErrors.title = "Team name cannot be 'new'"
				return false
			}
			return true
		},
		save() {
			const oldTeamName = this.team.name
			const newTeamName = this.newTeamValues.title
			const values = this.newTeamValues
			let users = []
			values.users.map((user) => {
				users.push({
					user,
				})
			})
			if (this.teamId) {
				this.$resources.team.setValue
					.submit({
						team_name: values.title,
						users,
					})
					.then(() => {
						if (newTeamName != oldTeamName) {
							this.$resources.renameTeamDoc.submit({
								doctype: "Agent Group",
								old_name: oldTeamName,
								new_name: newTeamName,
							})
						}
					})
			} else {
				this.$resources.newTeam.submit({
					doc: {
						doctype: "Agent Group",
						team_name: values.title,
						users,
					},
				})
			}
		},
		cancel() {
			this.$router.go()
		},
	},
}
</script>
