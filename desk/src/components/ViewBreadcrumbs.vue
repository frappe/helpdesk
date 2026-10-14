<template>
  <div class="flex items-center">
    <router-link
      :to="{ name: routeName }"
      class="ps-0 pe-0.5 py-1 text-lg-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-5 hover:text-ink-gray-7 flex items-center justify-center"
    >
      {{ isMobileView ? "..." : label }}
    </router-link>
    <span class="ml-0.5 text-base text-ink-gray-4" aria-hidden="true"> / </span>
    <Dropdown v-model:open="isOpen" :options="options">
      <template #default="{ open }">
        <Button
          variant="ghost"
          class="max-w-[200px] sm:max-w-none !bg-transparent hover:!bg-surface-gray-3 focus-visible:!ring-0"
          :class="open && '!bg-surface-gray-3'"
        >
          <span class="text-lg-medium text-nowrap truncate">{{
            currentView.label
          }}</span>
          <template #prefix>
            <component
              :is="currentView.icon"
              class="flex size-4 shrink-0 items-center justify-center"
            />
          </template>
          <template #suffix>
            <component
              :is="open ? LucideChevronUp : LucideChevronDown"
              class="h-4 text-ink-gray-8"
            />
          </template>
        </Button>
      </template>

      <template #item-prefix="{ item }">
        <Icon
          v-if="item.icon"
          :icon="item.icon"
          class="h-4 w-4 flex-shrink-0 text-ink-gray-7"
          aria-hidden="true"
        />
      </template>

      <template #item-label="{ item }">
        <div class="flex items-center min-w-0 max-w-[50vw]">
          <span class="truncate">{{ item.label }}</span>
          <Badge
            v-if="item.is_standard"
            class="ms-1 flex-shrink-0"
            size="sm"
            label="Standard"
          />
        </div>
      </template>
      <template #item-suffix="{ item }">
        <div
          v-if="item.name"
          class="flex items-center justify-end gap-2 min-w-11"
        >
          <LucideCheck
            v-if="isCurrentView(item)"
            class="size-4 text-ink-gray-7"
          />
          <!-- -my-0.5: at its full height the button would make the row 4px
               taller than the rows without one -->
          <Dropdown side="right" align="start" :options="viewActions(item)">
            <template #default="{ open }">
              <Button
                variant="ghost"
                class="kebab-btn !-my-0.5 !size-5 ms-0 !rounded-2"
                :class="open ? 'inline-flex' : 'hidden'"
                icon="lucide-more-horizontal"
                @click.stop
              />
            </template>
          </Dropdown>
        </div>
      </template>
    </Dropdown>
  </div>
</template>

<script setup>
import LucideChevronUp from "~icons/lucide/chevron-up";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucideCheck from "~icons/lucide/check";
import Icon from "@/components/Icon.vue";
import { useScreenSize } from "@/composables/screen";
import { Badge, Dropdown } from "frappe-ui";
import { ref } from "vue";
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
const isOpen = ref(false);

// Every kebab action opens a dialog, and popovers paint above dialogs, so this
// menu has to close itself first or it covers what it just opened.
const viewActions = (item) =>
  props.dropdownActions(item).map((group) => ({
    ...group,
    options: group.options.map((option) => ({
      ...option,
      onClick: () => {
        isOpen.value = false;
        option.onClick?.();
      },
    })),
  }));

const isCurrentView = (item) => {
  if (!route.query.view) return false;
  return item.name === route.query.view;
};
</script>

<style>
/* inline-flex, not block: the button centres its icon with flex */
[data-slot="item"][data-highlighted] .kebab-btn,
[data-slot="item"][data-state="checked"] .kebab-btn {
  display: inline-flex;
}

/* --fade-top / --fade-bottom + scroll-fade keyframes live in src/index.css */
[data-slot="group"]:has(.kebab-btn) {
  @apply sm:max-h-80 max-h-40 overflow-y-auto overscroll-contain;
  -webkit-mask-image: linear-gradient(
    to bottom,
    black calc(100%),
    transparent 100%
  );
  mask-image: linear-gradient(to bottom, black calc(100%), transparent 100%);
  animation: scroll-fade linear both;
  animation-timeline: scroll(self);
}

/* keep the group label pinned while its items scroll */
[data-slot="group"]:has(.kebab-btn) [data-slot="group-label"] {
  @apply sticky -top-[6px] z-10 bg-surface-elevation-2;
}
</style>
