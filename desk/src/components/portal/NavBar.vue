<template>
	<div class="py-4">
		<div class="container mx-auto">
			<div class="flex flex-row justify-between items-center">
				<div class="flex flex-row">
					<div class="flex space-x-1">
						<CustomIcons name="company" class="h-7 w-7"/>
					</div>
				</div>
				<div class="flex space-x-8 text-[14px] text-[#4C5A67] items-center">
					<div v-for="item in navbarItems" :key="item.label">
						<a :href="item.url" class="hover:text-[#2490ef]">{{ item.label }}</a>
					</div>
					<CustomAvatar :label="user.username" class="cursor-pointer" size="xl" v-if="user" :imageURL="user.profile_image" />
				</div>
			</div>
		</div>
	</div>
</template>
<script>
import { Dropdown, call } from 'frappe-ui'
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
		}
	},
	methods: {
		async logout() {
			await call('logout')
			window.location.replace("/login");
		},
        ticketTemplateOptions() {
			let templateItems = [];
			if (this.ticketTemplates) {
				this.ticketTemplates.forEach(template => {
					templateItems.push({
						label: template.name,
						handler: () => {
							this.$router.push({
								name: 'TemplatedNewTicket',
								params: {
									templateId: template.template_route
								}
							})
						},
					});
				});
				return templateItems.length > 1 ? templateItems : [];
			} else {
				return null;
			}
		},
		openDefaultTicketTemplate() {
			this.$router.push({
				name: 'DefaultNewTicket'
			})
		}
	}
}
</script>