<template>
	<div class="flow-root pl-5 pr-8 border-b py-2">
		<div class="float-left py-1.5">
			<div class="flex space-x-1">
				<CustomIcons name="frappedesk" width="60" height="18"/>
				<div v-if="breadcrumbs" class="flex items-center space-x-1">
					<div v-for="(breadcrumb, index) in breadcrumbs" :key="breadcrumb">
						<div class="flex space-x-1 items-center text-base" :class="breadcrumb.path ? 'cursor-pointer' : ''" @click="() => {breadcrumb.path ? routeTo(breadcrumb.path) : {}}">
							<FeatherIcon v-if="index < breadcrumbs.length" name="chevron-right" class="h-4 w-4" />
							<span :class="index == breadcrumbs.length - 1 ? 'text-gray-500' : ''">{{ breadcrumb.label }}</span>
						</div>
					</div>
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
import { Avatar, FeatherIcon, Dropdown } from 'frappe-ui'
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
		getAvatarClickOptions() {
			let items = [];
			["Log out"].forEach(item => {
				items.push({
				label: item,
					handler: () => {
						this.user.logout()
					},
				});
			});
			return items;
		},
		routeTo(path) {
			this.$router.push({path})
		},
	},
	computed: {
		breadcrumbs() {
			if (this.$route.meta.breadcrumbs) {
				return this.$route.meta.breadcrumbs(this.$route)
			} else {
				return []
			}
		},
	},
}
</script>