<template>
	<div>
		<SettingsTopPanel :selectedSetting="selectedSetting" />
		<div :style="{ height: viewportWidth > 768 ? 'calc(100vh - 55px)' : null }" class="flex">
			<div class="sm:w-2/12 border-r">
				<SettingsSideBarMenu />
			</div>
			<div class="sm:w-10/12 h-full">
				<router-view v-slot="{ Component }">
					<keep-alive>
						<component :is="Component" />
					</keep-alive>
				</router-view>
			</div>
		</div>
	</div>
</template>

<script>
import SettingsSideBarMenu from "@/components/desk/settings/SettingsSideBarMenu.vue"
import SettingsTopPanel from "@/components/desk/settings/SettingsTopPanel.vue"

import { inject, provide, ref } from 'vue'

export default {
	name: 'Settings',
	components: {
		SettingsSideBarMenu,
		SettingsTopPanel
	},
	setup() {
		const viewportWidth = inject('viewportWidth')
		const selectedSetting = ref('Agents')
		provide('selectedSetting', selectedSetting)

		return { viewportWidth, selectedSetting }
	},
}
</script>

<style>

</style>