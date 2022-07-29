<template>
    <div class="flex flex-col space-y-[16px] pt-[12px] text-[13px] font-normal select-none">
        <div class="border-b pl-[20px] pr-[6px] pb-[12px] flex flex-row space-x-2 items-center">
            <span class="grow font-semibold">Categories</span>
            <FeatherIcon @click="() => {}" name="plus" class="shrink-0 stroke-white bg-blue-500 rounded h-4 w-4 p-0.5" role="button"/>
        </div>
        <div class="overflow-y-scroll flex flex-col space-y-[16px]" style="height: calc(100vh - 113px)">
            <div v-for="category in categories" :key="category.name">
                <div v-if="category.is_group" class="pl-[20px] pr-[6px]">
                    <div 
                        role="button" 
                        class="flex flex-row items-center group space-x-2"
                    >
                        <div class="grow truncate" @click="() => { category.expanded = !category.expanded }">{{ category.name }}</div>
                        <FeatherIcon @click="() => {}" name="plus" class="shrink-0 stroke-gray-700 bg-gray-200 rounded h-4 w-4 p-0.5 hidden group-hover:block" />
                        <FeatherIcon @click="() => { category.expanded = !category.expanded }" :name="category.expanded ? 'chevron-up' : 'chevron-down'" class="h-4 w-4 shrink-0" />
                    </div>
                    <div v-if="category.expanded" class="pt-[16px] space-y-[16px] flex flex-col">
                        <div v-for="subCategory in category.children" :key="subCategory.name">
                            <div 
                                class="px-[12px] py-[4px] truncate rounded w-full" 
                                :class="subCategory.name === selectedCategory.name ? 'bg-gray-50' : ''" 
                                role="button"
                                @click="() => { selectedCategory = subCategory }"
                            > 
                                {{ subCategory.name }} 
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { ref } from 'vue'
import { FeatherIcon, Dropdown } from 'frappe-ui'

export default {
    components: {
        FeatherIcon,
        Dropdown,
    },
    setup() {       
        let categories = ref([])
        let selectedCategory = ref(null)

        return { categories, selectedCategory }
    },
    watch: {
        selectedCategory(category) {
            console.log(category)
            this.$router.push(`/frappedesk/knowledge-base/${category.parent_category}/${category.name}`)
        },
    },
    resources: {
        categories() {
            return {
                type: 'list',
                doctype: 'Category',
                fields: ['is_group', 'parent_category', 'name'],
                onSuccess: (list) => {
                    let categories = []
                    let expandedFlag = false
                    list.forEach(category => {
                        if (category.is_group) {
                            categories.push({...category, children: [], expanded: expandedFlag ? false : true})
                            expandedFlag = true
                        }
                    })
                    list.forEach(category => {
                        if (!category.is_group && category.parent_category && categories.find(c => c.name == category.parent_category)) {
                            if (!this.selectedCategory) {
                                this.selectedCategory = category
                            }
                            categories.find(c => c.name == category.parent_category).children.push(category)
                        }
                    })
                    this.categories = categories
                }
            }
        }
    }
}
</script>