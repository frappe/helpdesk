<template>
	<div>
		<SettingsTopPanel />
		<div
			:style="{
				height: viewportWidth > 768 ? 'calc(100vh - 55px)' : null,
			}"
			class="flex"
		>
			<div class="min-w-[180px] border-r">
				<SettingsSideBarMenu />
			</div>
			<div class="grow h-full">
				<router-view v-slot="{ Component }">
					<component :is="Component" />
				</router-view>
			</div>
		</div>
	</div>
</template>

<script>
import SettingsSideBarMenu from "@/components/desk/settings/SettingsSideBarMenu.vue"
import SettingsTopPanel from "@/components/desk/settings/SettingsTopPanel.vue"

import { inject } from "vue"

export default {
	name: "Settings",
	components: {
		SettingsSideBarMenu,
		SettingsTopPanel,
	},
	setup() {
		const viewportWidth = inject("viewportWidth")
		return {
			viewportWidth,
		}
	},
}
</script>

<style></style>
