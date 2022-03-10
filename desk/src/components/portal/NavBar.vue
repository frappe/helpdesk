<template>
	<div class="flow-root pl-5 pr-8 border-b py-4">
		<div class="float-left py-1.5">
			<div class="flex space-x-1">
				<CustomIcons name="helpdesk" width="60" height="18"/>
				<div v-if="$currentPage.breadcrumbs()" class="flex items-center space-x-1">
					<div v-for="(breadcrumb, index) in $currentPage.breadcrumbs()" :key="breadcrumb">
						<div class="flex space-x-1 items-center text-base">
							<FeatherIcon v-if="index < $currentPage.breadcrumbs().length" name="chevron-right" class="h-4 w-4" />
							<span>{{ breadcrumb }}</span>
						</div>
					</div>
				</div>
			</div>
		</div>
		<div class="float-right flex space-x-3 items-center">
			<Dropdown
                v-if="ticketTemplateOptions().length > 1"
                placement="right"
                :options="ticketTemplateOptions()"
                :dropdown-width-full="true"
            >
                <template v-slot="{ toggleTemplates }">
                    <div>
                        <div 
                            class="cursor-pointer"
                            @click="toggleTemplates"
                            icon-left="plus" 
                            appearance="primary"
                        >
                            Submit a ticket
                        </div>
                    </div>
                </template>
            </Dropdown>
            <router-link v-else  :to="{name: 'DefaultNewTicket'}" class="cursor-pointer">
                <div class="hover:text-gray-900 text-gray-600">Submit a ticket</div>
            </router-link>
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