<template>
	<div class="flex flex-col px-1 border-r pt-4" :style="{ height: viewportWidth > 768 ? 'calc(100vh)' : null }">
		<div class="space-y-5 mb-auto">
			<div class="group p-1 rounded-md pb-5">
				<CustomIcons name="helpdesk" width="40" height="40"/>
			</div>
			<div class="group p-3 hover:bg-blue-50 rounded-md cursor-pointer">
				<CustomIcons name="ticket" class="group-hover:stroke-blue-600" width="25" height="25"/>
			</div>
			<div class="group p-3 hover:bg-blue-50 rounded-md cursor-pointer">
				<CustomIcons name="knowledge-base" class="group-hover:stroke-blue-600" width="25" height="25"/>
			</div>
			<div class="group p-3 hover:bg-blue-50 rounded-md cursor-pointer">
				<CustomIcons name="customers" class="group-hover:stroke-blue-600" width="25" height="25"/>
			</div>
			<div class="group p-3 hover:bg-blue-50 rounded-md cursor-pointer">
				<CustomIcons name="reports" class="group-hover:stroke-blue-600" width="25" height="25"/>
			</div>
		</div>
		<div class="space-y-5 mt-auto">
			<div class="group p-3 hover:bg-blue-50 rounded-md cursor-pointer">
				<CustomIcons name="settings" class="group-hover:stroke-blue-600" width="25" height="25"/>
			</div>
		</div>
	</div>
</template>

<script>
import CustomIcons from "./CustomIcons.vue"

export default {
	name: 'SideBarMenu',
	inject: ['viewportWidth'],
	props: ['selectedMenuItem'],
	data() {
		return {
			iconHeight: 30,
			iconWidth: 30
		}
	},
	components: {
		CustomIcons
	}
}
</script>
