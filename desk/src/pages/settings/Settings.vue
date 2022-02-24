<template>
    <div :style="{ height: viewportWidth > 768 ? 'calc(100vh - 4.5rem)' : null }" class="flex">
        <div class="sm:w-2/12 h-full">
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
</template>

<script>
import SettingsSideBarMenu from "@/components/settings/SettingsSideBarMenu.vue"

export default {
    name: 'Settings',
    components: {
        SettingsSideBarMenu
    },
    inject: ['viewportWidth'],
	activated() {
		this.$currentPage.set('Settings')
	},
	deactivated() {

	},
}
</script>

<style>

</style>