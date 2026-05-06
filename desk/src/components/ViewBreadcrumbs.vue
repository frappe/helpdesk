<template>
  <div class="flex items-center">
    <router-link
      :to="{ name: routeName }"
      class="px-0.5 pl-0 py-1 text-lg font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-5 hover:text-ink-gray-7 flex items-center justify-center"
    >
      {{ isMobileView ? "..." : label }}
    </router-link>
    <span class="mx-0.5 text-base text-ink-gray-4" aria-hidden="true"> / </span>
    <Dropdown :options="options">
      <template #default="{ open }">
        <Button
          variant="ghost"
          class="text-lg font-medium text-nowrap truncate max-w-[200px] sm:max-w-none"
          :label="currentView.label"
        >
          <template #prefix>
            <component
              :is="currentView.icon"
              class="h-4 flex items-center justify-center"
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

      <template #item-prefix="{ item }">
        <FeatherIcon
          v-if="item.icon && typeof item.icon === 'string'"
          :name="item.icon"
          class="h-4 w-4 flex-shrink-0 text-ink-gray-7"
          aria-hidden="true"
        />
        <component
          class="h-4 w-4 flex-shrink-0 text-ink-gray-7"
          v-else-if="item.icon"
          :is="item.icon"
        />
      </template>

      <template #item-label="{ item }">
        <span class="whitespace-nowrap">{{ item.label }}</span>
        <Badge
          v-if="item.is_standard"
          class="ml-1"
          size="sm"
          label="Standard"
        />
      </template>
      <template #item-suffix="{ item }">
        <div
          v-if="item.name"
          class="flex flex-row-reverse gap-2 items-center min-w-11"
        >
          <Dropdown align="end" :options="dropdownActions(item)">
            <template #default>
              <Button
                variant="ghost"
                class="kebab-btn hidden !size-4 ml-0 rounded-sm"
                icon="more-horizontal"
                @click.stop
              />
            </template>
          </Dropdown>

          <FeatherIcon
            v-if="isCurrentView(item)"
            name="check"
            class="size-4 text-ink-gray-7"
          />
        </div>
      </template>
    </Dropdown>
  </div>
</template>

<script setup>
import { useScreenSize } from "@/composables/screen";
import { Badge, Dropdown } from "frappe-ui";
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

<style>
[data-slot="item"][data-highlighted] .kebab-btn,
[data-slot="item"][data-state="checked"] .kebab-btn {
  display: block;
}
</style>
