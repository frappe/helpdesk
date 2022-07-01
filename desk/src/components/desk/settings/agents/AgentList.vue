<template>
    <div>
        <div
            @pointerenter="() => { showSelectAllCheckbox = true}"
            @pointerleave="() => { showSelectAllCheckbox = false}"
            class="bg-[#F7F7F7] group flex items-center text-base font-medium text-gray-500 py-[10px] px-[11px] rounded-[6px] select-none"
        >
            <div class="w-[37px] h-[14px]">
                <Input 
                    type="checkbox" 
                    @click="manager.selectAll()" 
                    :checked="manager.allItemsSelected" 
                    class="cursor-pointer mr-1 hover:visible" 
                    :class="manager.allItemsSelected || showSelectAllCheckbox ? 'visible' : 'invisible'" 
                />
            </div>
            <div class="flex flex-row items-center group w-full">
                <div class="sm:w-6/12">
                    Name
                </div>
                <div class="sm:w-4/12">
                    Email
                </div>
                <div class="sm:w-4/12">
                    Roles
                </div>
                <div class="sm:w-4/12">
                    Team
                </div>
            </div>
        </div>
        <div 
            id="rows" 
            class="flex flex-col space-y-2 overflow-scroll"
            :style="{ height: viewportWidth > 768 ? 'calc(100vh - 120px)' : null }"
        >
            <div v-if="!manager.loading">
                <div v-if="manager.list.length > 0">
                    <div v-for="(agent, index) in manager.list" :key="agent.name">
                        <AgentListItem :class="index == 0 ? 'mt-[9px] mb-[2px]' : 'my-[2px]'" :agent="agent" @toggle-select="manager.select(agent)" :selected="manager.itemSelected(agent)" />
                    </div>
                </div>
                <div v-else>
                    <div class="grid place-content-center h-48 w-full">
                        <div>
                            <CustomIcons name="empty-list" class="h-12 w-12 mx-auto mb-2" />
                            <div class="text-gray-500 mb-2">No agents found</div>
                        </div>
                    </div>
                </div>
            </div>
            <ListPageController :manager="manager" />
        </div>
    </div>
</template>

<script>
import { ref, inject } from 'vue'
import { Input } from 'frappe-ui'
import AgentListItem from '@/components/desk/settings/agents/AgentListItem.vue'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import ListPageController from '@/components/global/ListPageController.vue'

export default {
    name: 'AgentList',
    props: ['manager'],
    components: {
        AgentListItem,
        CustomIcons,
        Input,
        ListPageController
    },
    setup() {
        const showSelectAllCheckbox = ref(false)
        const viewportWidth = inject('viewportWidth')
        return {
            showSelectAllCheckbox,
            viewportWidth
        }
    }
}
</script>

<style>

</style>