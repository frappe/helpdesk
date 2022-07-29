<template>
    <div class="flex flex-col">
        <TopNavbar class="h-[52px] border-b" />
        <div class="grow flex flex-row">
            <SideBarMenu class="w-[173px] shrink-0 border-r" />
            <router-view class="grow" />
        </div>
    </div>
</template>

<script>
import SideBarMenu from '@/components/desk/knowledge_base/SideBarMenu.vue'
import TopNavbar from '@/components/desk/knowledge_base/TopNavbar.vue'

export default {
    components: {
        SideBarMenu,
        TopNavbar,
    }
}
</script>

<style>

</style>