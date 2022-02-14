<template>
	<div class="flex flex-col" :style="{ height: viewportWidth > 768 ? 'calc(100vh - 6rem)' : null }">
		<div class="space-y-5 px-3 mb-auto">
			<div class="group p-2 hover:bg-blue-50 rounded-md cursor-pointer">
				<CustomIcons name="ticket" class="group-hover:stroke-blue-600" width="34" height="34"/>
			</div>
			<div class="group p-2 hover:bg-blue-50 rounded-md cursor-pointer">
				<CustomIcons name="knowledge-base" class="group-hover:stroke-blue-600" width="30" height="30"/>
			</div>
			<div class="group p-2 hover:bg-blue-50 rounded-md cursor-pointer">
				<CustomIcons name="customers" class="group-hover:stroke-blue-600" width="32" height="32"/>
			</div>
			<div class="group p-2 hover:bg-blue-50 rounded-md cursor-pointer">
				<CustomIcons name="reports" class="group-hover:stroke-blue-600" width="30" height="30"/>
			</div>
		</div>
		<div class="space-y-5 px-3 mt-auto">
			<div class="group p-2 hover:bg-blue-50 rounded-md cursor-pointer">
				<CustomIcons name="settings" class="group-hover:stroke-blue-600" width="30" height="30"/>
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
