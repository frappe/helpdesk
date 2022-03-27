<template>
	<div class="flex flex-col px-1 border-r pt-4" :style="{ height: viewportWidth > 768 ? 'calc(100vh - 3.9rem)' : null }">
		<div class="space-y-5 mb-auto">
			<div>
				<router-link to="/helpdesk/tickets">
					<div class="group p-3 hover:bg-blue-50 rounded-md cursor-pointer">
						<CustomIcons name="ticket" class="group-hover:stroke-blue-600" width="25" height="25"/>
					</div>
				</router-link>
			</div>
			<div v-if="false">
				<router-link to="/helpdesk/knowledge-base">
					<div class="group p-3 hover:bg-blue-50 rounded-md cursor-pointer">
						<CustomIcons name="knowledge-base" class="group-hover:stroke-blue-600" width="25" height="25"/>
					</div>
				</router-link>
			</div>
			<div>
				<router-link to="/helpdesk/contacts">
					<div class="group p-3 hover:bg-blue-50 rounded-md cursor-pointer">
						<CustomIcons name="customers" class="group-hover:stroke-blue-600" width="25" height="25"/>
					</div>
				</router-link>
			</div>
			<div v-if="false">
				<router-link to="/helpdesk/reports">
					<div class="group p-3 hover:bg-blue-50 rounded-md cursor-pointer">
						<CustomIcons name="reports" class="group-hover:stroke-blue-600" width="25" height="25"/>
					</div>
				</router-link>
			</div>
		</div>
		<div class="space-y-5 mt-auto mb-2">
			<div>
				<router-link to="/helpdesk/settings/agents">
					<div class="group p-3 hover:bg-blue-50 rounded-md cursor-pointer">
						<CustomIcons name="settings" class="group-hover:stroke-blue-600" width="25" height="25"/>
					</div>
				</router-link>
			</div>
		</div>
	</div>
</template>

<script>
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import { inject, ref } from 'vue'

export default {
	name: 'SideBarMenu',
	components: {
		CustomIcons
	},
	setup() {
		const viewportWidth = inject('viewportWidth')

		const iconHeight = ref(30)
		const iconWidth = ref(30)

		return { viewportWidth, iconHeight, iconWidth }
	}
}

</script>