<template>
	<div class="min-w-[490px] px-[24px] py-[10px]">
		<div class="shrink-0 h-[72px] py-[22px] flow-root px-[16px]">
			<div class="float-left">
				<router-link
					:to="`/frappedesk/settings/teams`"
					class="my-1 text-[12px] text-gray-600 stroke-gray-600 flex flex-row items-center space-x-1 hover:text-gray-700 hover:stroke-gray-700 select-none"
					role="button"
				>
					<FeatherIcon name="arrow-left" class="w-[13px] h-[13px]" />
					<div>Back to team list</div>
				</router-link>
			</div>
			<div class="float-right">
				<div class="flex flex-row space-x-2">
					<Button
						appearance="secondary"
						@click="
							() => {
								this.$router.go()
							}
						"
					>
						Cancel
					</Button>
					<Button appearance="primary" @click="saveDocument()">
						Save
					</Button>
				</div>
			</div>
		</div>
		<div
			class="flex flex-row space-x-[24px] h-full border-t px-[16px] py-[22px]"
		>
			<TeamTitleAndUsers
				class="grow"
				:name="values?.teamName"
				:users="usersValue"
				:editable="editMode"
				:teamResource="$resources.team"
			/>
		</div>
	</div>
</template>
<script>
import { ref, provide } from "vue"
import { FeatherIcon, Input } from "frappe-ui"
import TeamTitleAndUsers from "@/components/desk/settings/teams/TeamTitleAndUsers.vue"

export default {
	name: "TeamInfo",
	props: ["teamId"],
	components: {
		FeatherIcon,
		Input,
		TeamTitleAndUsers,
	},
	setup(props) {
		const editingTitle = ref(false)
		const newTeamTempValues = ref({})
		const updateNewTeamInput = ref((input) => {
			newTeamTempValues.value[input.field] = input.value
		})
		provide("updateNewTeamInput", updateNewTeamInput)
		provide("newTeamTempValues", newTeamTempValues)
		const saveTeamTitleAndUsers = ref(() => {})
		provide("saveTeamTitleAndUsers", saveTeamTitleAndUsers)
		const tempTeamTitle = ref("")
		const updatingValues = ref(false)
		const editMode = ref(!props.teamId)
		provide("editMode", editMode)

		return {
			editingTitle,
			tempTeamTitle,
			updatingValues,
			editMode,
			newTeamTempValues,
			saveTeamTitleAndUsers,
		}
	},
	computed: {
		teamDoc() {
			return this.$resources.team.doc || null
		},
		values() {
			if (this.updatingValues) {
				return this.values || null
			}
			return {
				teamName: this.teamDoc?.team_name || null,
			}
		},
		usersValue() {
			let options = []
			this.teamDoc.users?.map((res) => {
				let value = {}
				value["user"] = res["user"]

				options.push(value)
			})

			return options
		},
	},
	deactivated() {
		this.resetForm()
	},
	resources: {
		team() {
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
	},
	methods: {
		resetForm() {
			this.editingTitle = false
			this.tempTeamTitle = this.values.teamName
		},
		save() {
			this.updatingValues = true
			const newValues = this.values
			const newUsers = this.usersValue
			this.$resources.user.setValue
				.submit({
					team_name: newValues.title,
					users: newUsers,
				})
				.then(() => {
					this.$resources.team.setValue.submit({
						team_name: this.tempTeamTitle,
					})
				})
		},
		saveDocument() {
			const inputParams = {
				team_name: this.newTeamTempValues.title,
				users: this.newTeamTempValues.users,
			}
			this.$resources.team.setValue.submit({
				...inputParams,
			})
			this.editMode = false
		},
		cancel() {
			this.$router.go()
		},
	},
}
</script>
