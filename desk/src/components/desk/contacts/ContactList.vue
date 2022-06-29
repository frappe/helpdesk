<template>
    <div>
        <div
            @pointerenter="() => { showSelectAllCheckbox = true}"
            @pointerleave="() => { showSelectAllCheckbox = false}"
            class="bg-[#F7F7F7] group flex items-center text-base font-medium text-gray-500 py-[10px] pl-[11px] pr-[49.80px] rounded-[6px] select-none"
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
            <div 
                class="sm:w-1/12 flex flex-row items-center space-x-[7px] cursor-pointer"
                @click="manager.toggleOrderBy('name')"
            >
                <span>#</span>
            </div>
            <div 
                class="sm:w-8/12 flex flex-row items-center space-x-[6px] cursor-pointer"
                @click="manager.toggleOrderBy('subject')"
            >
                <span>Subject</span>
            </div>
            <div 
                class="sm:w-3/12 flex flex-row items-center space-x-[6px] cursor-pointer"
                @click="manager.toggleOrderBy('status')"
            >
                <span>Status</span>
            </div>
            <div 
                class="sm:w-3/12 flex flex-row items-center space-x-[6px] cursor-pointer"
                @click="manager.toggleOrderBy('contact')"
            >
                <span>Created By</span>
            </div>
            <div 
                class="sm:w-2/12 flex flex-row items-center space-x-[6px] cursor-pointer"
                @click="manager.toggleOrderBy('resolution_by')"
            >
                <span>Due In</span>
            </div>
            <div
                class="sm:w-1/12 flex flex-row items-center space-x-[6px] cursor-pointer"
                @click="manager.toggleOrderBy('modified')"
            >
                <span>Modified</span>
            </div>
        </div>
        <div 
            id="rows" 
            class="flex flex-col space-y-2 overflow-scroll"
            :style="{ height: viewportWidth > 768 ? 'calc(100vh - 6.4rem)' : null }"
        >
            <div v-if="!manager.loading">
                <div v-if="manager.list.length > 0">
                    <div v-for="contact in manager.list" :key="contact.name">
                        <ContactListItem :contact="contact" @toggle-select="manager.select(contact)" :selected="manager.itemSelected(contact)" />
                    </div>
                </div>
                <div v-else>
                    <div class="grid place-content-center h-48 w-full">
                        <div>
                            <CustomIcons name="empty-list" class="h-12 w-12 mx-auto mb-2" />
                            <div class="text-gray-500 mb-2">No contacts found</div>
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
import ContactListItem from '@/components/desk/contacts/ContactListItem.vue'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import ListPageController from '@/components/global/ListPageController.vue'

export default {
    name: 'ContactList',
    props: ['manager'],
    components: {
        ContactListItem,
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