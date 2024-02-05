<template>
  <div class="flex items-center justify-between p-4">
    <div class="flex-none">
      <Dropdown :options="[{ label: 'List View', icon: 'list' }]">
        <template #default="{ open }">
          <Button label="List View">
            <template #prefix>
              <FeatherIcon name="list" class="h-4" />
            </template>
            <template #suffix>
              <FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4 text-gray-600"
              />
            </template>
          </Button>
        </template>
      </Dropdown>
    </div>

    <div class="grow"></div>

    <div class="flex-none px-1">
      <Filter
        :filters="props.filter.filters"
        :filterable-fields="props.filter.filterableFields"
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
import { Filter } from "@/components";
import { Dropdown, FeatherIcon } from "frappe-ui";

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
