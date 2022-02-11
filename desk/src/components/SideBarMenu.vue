<template>
	<div class="space-y-5 px-3">
		<div class="group p-2 hover:bg-blue-50 rounded-md cursor-pointer">
			<CustomIcons name="ticket" class="hover:stroke-blue-600" width="34" height="34"/>
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
</template>

<script>
import CustomIcons from "./CustomIcons.vue"

export default {
	name: 'SideBarMenu',
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
