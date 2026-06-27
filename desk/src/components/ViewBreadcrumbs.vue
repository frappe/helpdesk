<template>
  <div class="flex items-center">
    <router-link
      :to="{ name: routeName }"
      class="ps-0 pe-0.5 py-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-5 hover:text-ink-gray-7 flex items-center justify-center text-lg-medium"
    >
      {{ isMobileView ? "..." : label }}
    </router-link>
    <span class="mx-0.5 text-base text-ink-gray-4" aria-hidden="true"> / </span>
    <Dropdown :options="options">
      <template #default="{ open }">
        <button
          type="button"
          class="group flex items-center rounded px-0.5 py-1 text-lg-medium text-ink-gray-8 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 max-w-[200px] sm:max-w-none"
        >
          <component
            :is="currentView.icon"
            class="me-1 h-4 flex items-center justify-center self-center"
          />
          <span class="truncate group-hover:underline">
            {{ currentView.label }}
          </span>
          <span
            :class="[
              'ms-0.5 h-4 text-ink-gray-5',
              open ? 'lucide-chevron-up' : 'lucide-chevron-down',
            ]"
            aria-hidden="true"
          />
        </button>
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
          <span
            v-if="isCurrentView(item)"
            class="lucide-check size-4 text-ink-gray-7"
            aria-hidden="true"
          />
          <Dropdown align="end" :options="dropdownActions(item)">
            <template #default="{ open }">
              <Button
                variant="ghost"
                class="kebab-btn !size-4 ms-0 rounded-sm"
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
import Icon from "@/components/Icon.vue";
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

/* --fade-top / --fade-bottom + scroll-fade keyframes live in src/index.css */
[data-slot="group"]:has(.kebab-btn) {
  @apply sm:max-h-80 max-h-40 overflow-y-auto overscroll-contain;
  -webkit-mask-image: linear-gradient(
    to bottom,
    black calc(100% - var(--fade-bottom)),
    transparent 100%
  );
  mask-image: linear-gradient(
    to bottom,
    black calc(100% - var(--fade-bottom)),
    transparent 100%
  );
  animation: scroll-fade linear both;
  animation-timeline: scroll(self);
}

/* keep the group label pinned while its items scroll */
[data-slot="group"]:has(.kebab-btn) [data-slot="group-label"] {
  @apply sticky -top-[6px] z-10 bg-surface-elevation-2;
}
</style>
