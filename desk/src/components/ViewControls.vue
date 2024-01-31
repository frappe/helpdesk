<template>
    <div class="flex justify-between items-center p-4">
        <div class="flex-none">
            <p class="text-lg font-bold">List</p>
        </div>
    
        <div class="flex-grow"></div>
    
        <div class="flex-none pe-2">
            <Filter
                :filters="props.filter.filters" 
                :filterableFields ="props.filter.filterableFields" 
                @event:filter="emitToParent"
            />
        </div>
        <!-- <div class="flex-none pe-2">
            <p class="text-lg">Sort</p>
        </div>
        <div class="flex-none pe-2">
            <p class="text-lg">View Settings</p>
        </div> -->
    </div>
    </template>
    
    <script setup lang="ts">
    import { Filter } from '@/components';
    
    const props = defineProps({
      filter: {
        type: Object,
        required: true,
      },
    });
    
    const emit = defineEmits(["event:filter"]);
    
    function emitToParent(data) {
      emit("event:filter", data);
    }
    
    </script>