<template>
  <div class="flex items-center -ml-0.5">
    <router-link
      :to="{ name: routeName }"
      class="px-0.5 py-1 text-lg font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-5 hover:text-ink-gray-7 flex items-center justify-center"
    >
      {{ isMobileView ? "..." : label }}
    </router-link>
    <span class="mx-0.5 text-base text-ink-gray-4" aria-hidden="true"> / </span>
    <Dropdown :options="options">
      <template #default="{ open }">
        <Button
          variant="ghost"
          class="text-lg font-medium text-nowrap"
          :label="currentView.label"
        >
          <template #prefix>
            <Icon
              :icon="currentView.icon"
              class="h-4"
              v-if="typeof currentView.icon == 'string'"
            />
            <component
              :is="currentView.icon"
              class="h-4 flex items-center justify-center"
              v-else
            />
          </template>
          <template #suffix>
            <FeatherIcon
              :name="open ? 'chevron-up' : 'chevron-down'"
              class="h-4 text-ink-gray-8"
            />
          </template>
        </Button>
      </template>
      <template #item="{ item, active }">
        <button
          class="group flex text-ink-gray-6 gap-4 h-7 w-full justify-between items-center rounded px-2 text-base"
          :class="{ 'bg-surface-gray-3': active }"
          @click="item.onClick"
        >
          <div class="flex items-center">
            <FeatherIcon
              v-if="item.icon && typeof item.icon === 'string'"
              :name="item.icon"
              class="mr-2 h-4 w-4 flex-shrink-0 text-ink-gray-7"
              aria-hidden="true"
            />
            <component
              class="mr-2 h-4 w-4 flex-shrink-0 text-ink-gray-7"
              v-else-if="item.icon"
              :is="item.icon"
            />
            <span class="whitespace-nowrap">
              {{ item.label }}
            </span>
          </div>
          <div class="flex flex-row-reverse gap-2 items-center min-w-11">
            <Dropdown
              v-if="item.name"
              :class="active ? 'block' : 'hidden'"
              placement="right-start"
              :options="dropdownActions(item)"
            >
              <template #default="{ togglePopover }">
                <Button
                  variant="ghost"
                  class="!size-5"
                  icon="more-horizontal"
                  @click.stop="togglePopover()"
                />
              </template>
            </Dropdown>
            <FeatherIcon
              v-if="isCurrentView(item)"
              name="check"
              class="size-4 text-ink-gray-7"
            />
          </div>
        </button>
      </template>
    </Dropdown>
  </div>
</template>

<script setup>
import Dropdown from "@/components/frappe-ui/Dropdown.vue";
import { useScreenSize } from "@/composables/screen";
import { Icon } from "@iconify/vue";
import { useRoute } from "vue-router";

const props = defineProps({
  routeName: {
    type: String,
    required: true,
  },
  label: {
    type: String,
    required: true,
  },
  options: {
    type: Array,
    required: true,
  },
  dropdownActions: {
    type: Function,
    required: true,
  },
  currentView: {
    type: Object,
    required: true,
  },
});

const route = useRoute();
const { isMobileView } = useScreenSize();
const isCurrentView = (item) => {
  if (!route.query.view) return false;
  return item.name === route.query.view;
};
</script>
