<template>
	<div class="min-w-[490px] px-[24px] py-[10px]">
		<div class="flow-root h-[72px] shrink-0 py-[22px] px-[16px]">
			<div class="float-left">
				<router-link
					:to="`/helpdesk/dashboard/settings/teams`"
					class="my-1 flex select-none flex-row items-center space-x-1 stroke-gray-600 text-[12px] text-gray-600 hover:stroke-gray-700 hover:text-gray-700"
					role="button"
				>
					<FeatherIcon name="arrow-left" class="h-[13px] w-[13px]" />
					<div>Back to team list</div>
				</router-link>
			</div>
			<div class="float-right">
				<div class="flex flex-row space-x-2">
					<Button appearance="secondary" @click="cancel">Cancel</Button>
					<Button appearance="primary" @click="onSave">Save</Button>
				</div>
			</div>
		</div>
		<div
			v-if="team"
			class="flex h-full flex-row space-x-[24px] border-t px-[16px] py-[22px]"
		>
			<div class="flex h-full w-full flex-col space-y-[16px]">
				<div>
					<Input
						label="Title"
						type="text"
						:value="teamDisplayName(team)"
						@input="onNameChange"
					/>
					<ErrorMessage :message="teamInputErrors['title']" />
				</div>
				<form
					class="flex flex-row items-end space-x-2"
					@submit.prevent="onSubmit"
				>
					<div class="w-full space-y-1">
						<div>
							<span class="block text-sm leading-4 text-gray-700"> Users </span>
						</div>
						<Autocomplete
							id="searchInput"
							:value="''"
							:resource-options="autoCompleteOptions"
							@change="onAutocompleteChange"
						/>
					</div>
				</form>
				<div
					class="flex max-h-[300px] min-h-[100px] flex-col overflow-y-auto rounded border bg-gray-100 px-2"
				>
					<ul class="flex flex-wrap gap-2 py-2">
						<li
							v-for="user in team.users"
							:key="user"
							class="flex items-center space-x-2 rounded bg-white p-1 shadow"
						>
							<span class="ml-2 text-base">
								{{ userDisplayName(user) }}
							</span>
							<button
								class="grid h-4 w-4 place-items-center rounded text-gray-700 hover:bg-gray-300"
								@click="() => onUserClick(user)"
							>
								<FeatherIcon class="w-3" name="x" />
							</button>
						</li>
					</ul>
				</div>
				<div class="w-max">
					<Tooltip
						text="Agents belonging to this group can ignore any restrictions"
					>
						<Input
							v-model="team.ignore_restrictions"
							label="Ignore Restrictions"
							type="checkbox"
						/>
					</Tooltip>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { ref } from "vue";
import { FeatherIcon, ErrorMessage, Tooltip } from "frappe-ui";
import Autocomplete from "@/components/global/Autocomplete.vue";

export default {
	name: "TeamInfo",
	components: {
		Autocomplete,
		ErrorMessage,
		FeatherIcon,
		Tooltip,
	},
	props: {
		teamId: {
			type: String,
			default: "",
		},
	},
	setup() {
		const isTeamNameChanged = false;
		const team = ref({
			ignore_restrictions: false,
			team_name: "",
			users: [],
		});
		const teamInputErrors = ref({
			title: "",
		});

		return {
			isTeamNameChanged,
			team,
			teamInputErrors,
		};
	},
	data() {
		return {
			autoCompleteOptions: {
				url: "helpdesk.extends.client.get_list",
				inputMap: (query) => {
					return {
						doctype: "HD Agent",
						fields: ["name", "agent_name"],
						filters: {
							name: ["like", `%${query}%`],
						},
					};
				},
				responseMap: (res) => {
					return res.map((data) => {
						return {
							label: data.agent_name,
							value: data.name,
						};
					});
				},
			},
		};
	},
	resources: {
		team() {
			if (!this.teamId) return;

			return {
				type: "document",
				doctype: "HD Team",
				name: this.teamId,
				fields: ["name", "users"],
				whitelistedMethods: {
					renameTeam: "rename_self",
				},
				onSuccess(data) {
					// Only need user's name, not full object
					data.users = data.users.map((user) => user.user);
					this.team = data;
				},
				onError: (err) => {
					this.$toast({
						title: "Error Fetching Team",
						text: err,
						icon: "x",
						iconClasses: "text-red-500",
					});
				},
				setValue: {
					onSuccess: () => {
						this.$toast({
							title: "Team Updated",
							icon: "check",
							iconClasses: "text-green-500"
						});
					},
					onError: (err) => {
						this.$toast({
							title: "Error While Updating Ticket Type",
							text: err,
							icon: "x",
							iconClasses: "text-red-500",
						});
					},
				},
			};
		},
		newTeam() {
			return {
				url: "frappe.client.insert",
				onSuccess: (res) => {
					this.$router.push({
						path: `/helpdesk/dashboard/settings/teams/${res.name}`,
					});

					this.$toast({
						title: "New Team Created",
						icon: "check",
						iconClasses: "text-green-500",
					});
				},
			};
		},
	},
	methods: {
		validate() {
			const teamName = this.team.team_name;

			if (teamName === "") {
				this.teamInputErrors.title = "Team name is required";
				return false;
			}

			if (teamName.toLowerCase() === "new") {
				this.teamInputErrors.title = `Team name cannot be '${teamName}'`;
				return false;
			}

			return true;
		},
		renameTeam() {
			if (!this.isTeamNameChanged) return;

			const title = this.team.team_name;

			this.$resources.team.renameTeam
				.submit({
					new_name: title,
				})
				.then(() => {
					this.$router.push({
						path: `/helpdesk/dashboard/settings/teams/${title}`,
					});
				});
		},
		teamDisplayName(team) {
			if (team.team_name) return team.team_name;
			if (team.name) return team.name;
			if (this.teamId) return this.teamId;
		},
		/**
		 * What to show in user list. This has to be done because some users may not
		 * be fully loaded, and only ID will be available.
		 * @param {String|Object} user the user object, or just the ID
		 */
		userDisplayName(user) {
			return user.user ? user.user : user;
		},
		/**
		 * Map user list to be used in frappe client
		 * eg: `['mail@example.com']` -> `[{ 'user': 'mail@example.com' }]`
		 * @param {any} users Original list of users, this is not modified
		 * @returns {Array} Mapped list of users
		 */
		mapUsers(users) {
			return users.map((user) => ({ user }));
		},
		saveNew() {
			this.$resources.newTeam.submit({
				doc: {
					doctype: "HD Team",
					ignore_restrictions: this.team.ignore_restrictions,
					team_name: this.team.team_name,
					users: this.mapUsers(this.team.users),
				},
			});
		},
		save() {
			this.$resources.team.setValue
				.submit({
					ignore_restrictions: this.team.ignore_restrictions,
					users: this.mapUsers(this.team.users),
				})
				.then(this.renameTeam);
		},
		onNameChange(value) {
			this.isTeamNameChanged = this.team.team_name !== value;
			this.team.team_name = value;
		},
		onAutocompleteChange(item) {
			const user = item.value;
			const isUserInList = this.team.users.includes(user);

			if (isUserInList) return;

			this.team.users.push(user);
		},
		onUserClick(user) {
			this.team.users = this.team.users.filter((u) => u !== user);
		},
		cancel() {
			this.$router.go();
		},
		onSave() {
			if (!this.validate()) return;

			if (!this.$resources.team) {
				this.saveNew();
				return;
			}

			this.save();
		},
	},
};
</script>
