<template>
	<div class="py-4">
		<div class="container mx-auto">
			<div class="flex flex-wrap justify-between items-center">
				<div class="flex flex-row">
					<div class="flex space-x-1">
						<a href="/"><CustomIcons name="company" class="h-7 w-7"/></a>
					</div>
				</div>
				<div class="flex space-x-8 text-[14px] text-[#4C5A67] items-center">
					<div v-for="item in navbarItems" :key="item.label">
						<a :href="item.url" class="hover:text-[#2490ef]">{{ item.label }}</a>
					</div>
					<Dropdown
						placement="right"
						:options="profileOptions"
						:dropdown-width-full="true"
					>
						<template v-slot="{ toggleDropdown }">
							<CustomAvatar 
								v-if="user" 
								@click="toggleDropdown" 
								:label="user.username" 
								class="cursor-pointer" 
								size="xl" 
								:imageURL="user.profile_image" 
							/>
						</template>
					</Dropdown>
				</div>
			</div>
		</div>
	</div>
</template>
<script>
import { Dropdown } from 'frappe-ui'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import CustomAvatar from '../global/CustomAvatar.vue'
import { inject } from 'vue'

export default {
	name: 'NavBar',
	components: {
		CustomIcons,
		CustomAvatar,
		Dropdown
	},
	setup() {
		const user = inject('user')
		const ticketTemplates = inject('ticketTemplates')

		return { user, ticketTemplates }
	},
	resources: {
		navbarItems() {
			return {
				method: 'frappedesk.api.website.navbar_items',
				auto: true,
			}
		}
	},
	computed: {
		navbarItems() {
			return this.$resources.navbarItems.data || []
		},
		profileOptions() {
			return [
				{label: "My Account", handler: () => { window.location.href = '/me'} }, 
				{label: "Logout", handler: () => {
					this.user?.logout()
					window.location.href = '/support/login'
				}}
			];
		}
	},
}
</script>