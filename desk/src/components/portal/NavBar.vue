<template>
	<div class="flow-root pl-5 pr-8 border-b py-4">
		<div class="float-left">
			<div class="flex space-x-1">
				<CustomIcons name="company" class="h-7 w-7"/>
			</div>
		</div>
		<div class="float-right flex space-x-3">
			<div v-for="item in navbarItems" :key="item.label">
				{{ item.label }}
			</div>
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