<template>
	<div class="flow-root pb-3 pt-4 pl-5 pr-8 border-b">
		<div class="float-left">
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
		<div class="float-right flex space-x-3">
			<div class="border-r-2 pr-2 pt-1">
				<FeatherIcon class="w-5 h-5" name="bell" />
			</div>
			<Avatar v-if="$user.get()" :imageURL="$user.get().profile_image" />
		</div>
	</div>
</template>
<script>
import { Avatar, FeatherIcon, Dropdown } from 'frappe-ui'
import CustomIcons from './global/CustomIcons.vue'

export default {
	name: 'NavBar',
	components: {
		Avatar,
		FeatherIcon,
		CustomIcons,
		Dropdown
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
		}
	}
}
</script>