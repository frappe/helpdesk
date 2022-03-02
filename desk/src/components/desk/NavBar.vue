<template>
	<div class="flow-root pb-3 pt-4 pl-5 pr-8 border-b">
		<div class="float-left">
			<div class="flex items-center space-x-5">
				<div class="group rounded-md">
					<CustomIcons name="helpdesk" width="60" height="20"/>
				</div>
				<div v-if="$currentPage.get() == 'Tickets'">
					<Dropdown
						placement="left"
						:options="ticketFilterDropdownOptions()"
					>
						<template v-slot="{ toggleDropdown }"> 
							<div class="flex items-center" @click="toggleDropdown">
								<div class="text-2xl">
									{{ this.$ticketFilter.get() }}
								</div>
								<FeatherIcon class="ml-2 stroke-slate-600 h-5 w-5" name="chevron-down"/>
							</div>
						</template>
					</Dropdown>
				</div>
				<div v-else-if="$currentPage.get() == 'Contacts'">
					<Dropdown
						placement="left"
						:options="contactFilterDropdownOptions()"
					>
						<template v-slot="{ toggleDropdown }"> 
							<div class="flex items-center" @click="toggleDropdown">
								<div class="text-2xl">
									{{ this.$contactFilter.get() }}
								</div>
								<FeatherIcon class="ml-2 stroke-slate-600 h-5 w-5" name="chevron-down"/>
							</div>
						</template>
					</Dropdown>
				</div>
			</div>
		</div>
		<div class="float-right flex space-x-3">
			<div class="border-r-2 pr-2 pt-1">
				<FeatherIcon class="w-5 h-5" name="bell" />
			</div>
			<Dropdown
				:options="getAvatarClickOptions()" 
			>
				<template v-slot="{ toggleAssignees }" @click="toggleAssignees">
					<Avatar :label="user.username" class="cursor-pointer" v-if="user" :imageURL="user.profile_image" />
				</template>
			</Dropdown>
		</div>
	</div>
</template>
<script>
import { Avatar, FeatherIcon, Dropdown, call } from 'frappe-ui'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import { inject } from 'vue'

export default {
	name: 'NavBar',
	components: {
		Avatar,
		FeatherIcon,
		CustomIcons,
		Dropdown
	},
	setup() {
		const user = inject('user')

		return { user }
	},
	methods: {
		ticketFilterDropdownOptions() {
			let items = [];
			["All Tickets", "Assigned to me"].forEach(filter => {
				items.push({
					label: filter,
					handler: () => {
						console.log(this.$user);
						this.$ticketFilter.set(filter);
					}
				});
			});
			return items;
		},
		contactFilterDropdownOptions() {
			let items = [];
			["All Contacts"].forEach(filter => {
				items.push({
					label: filter,
					handler: () => {
						console.log(this.$user);
						this.$contactFilter.set(filter);
					}
				});
			});
			return items;
		},
		getAvatarClickOptions() {
			let items = [];
			["Logout"].forEach(item => {
				items.push({
				label: item,
					handler: () => {
						this.logout()
					},
				});
			});
			return items;
		},
		async logout() {
			await call('logout')
			window.location.replace("/login");
		}
	}
}
</script>