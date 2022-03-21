<template>
	<div class="flow-root pl-5 pr-8 border-b py-2">
		<div class="float-left py-1.5">
			<div class="flex space-x-1">
				<CustomIcons name="helpdesk" width="60" height="18"/>
				<div v-if="$currentPage.breadcrumbs()" class="flex items-center space-x-1">
					<div v-for="(breadcrumb, index) in $currentPage.breadcrumbs()" :key="breadcrumb">
						<div class="flex space-x-1 items-center text-base" :class="breadcrumb.action ? 'cursor-pointer' : ''" @click="() => {breadcrumb.action ? breadcrumb.action() : {}}">
							<FeatherIcon v-if="index < $currentPage.breadcrumbs().length" name="chevron-right" class="h-4 w-4" />
							<span :class="index == $currentPage.breadcrumbs().length - 1 ? 'text-gray-500' : ''">{{ breadcrumb.label }}</span>
						</div>
					</div>
				</div>
				<div v-if="$currentPage.get() == 'Contacts'">
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
		<div class="float-right flex space-x-3 items-center">
			<div class="border-r-2 pr-2">
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
			["Log out"].forEach(item => {
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