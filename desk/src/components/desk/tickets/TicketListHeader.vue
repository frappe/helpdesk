<template>
    <div 
        @pointerenter="() => { showSelectAllCheckbox = true }"
        @pointerleave="() => { showSelectAllCheckbox = false }"
        class="bg-[#F7F7F7] group flex items-center text-base font-medium text-gray-500 py-[10px] pl-[11px] pr-[49.80px] rounded-[6px]"
    >
        <Input 
            type="checkbox" 
            @click="toggleSelectAllTickets()" 
            :checked="allTicketsSelected" 
            class="cursor-pointer mr-2 hover:visible" 
            :class="allTicketsSelected || showSelectAllCheckbox ? 'visible' : 'invisible'" 
        />
        <div class="sm:w-1/12 flex items-baseline space-x-[7px]">
            <span>#</span>
            <CustomIcons 
                class="h-[6px] fill-gray-400 stroke-transparent" 
            />
        </div>
        <div class="sm:w-8/12 flex items-baseline space-x-[6px]">
            <span>Subject</span>
            <CustomIcons 
                class="h-[6px] fill-gray-400 stroke-transparent" 
            />
        </div>
        <div class="sm:w-2/12 flex items-baseline space-x-[6px]">
            <span>Status</span>
            <CustomIcons 
                class="h-[6px] fill-gray-400 stroke-transparent" 
            />
        </div>
        <div class="sm:w-3/12 flex items-baseline space-x-[6px]">
            <span>Created By</span>
            <CustomIcons 
                class="h-[6px] fill-gray-400 stroke-transparent"
            />
        </div>
        <div class="sm:w-2/12 flex items-baseline space-x-[6px]">
            <span>Due In</span>
            <CustomIcons 
                class="h-[6px] fill-gray-400 stroke-transparent" 
            />
        </div>
        <div class="sm:w-1/12 flex items-baseline space-x-[6px]">
            <span>Modified</span>
            <CustomIcons 
                class="h-[6px] fill-gray-400 stroke-transparent" 
            />
        </div>
    </div>
</template>

<script>
export default {

}
</script>

<style>

</style>