<template>
  <!-- Same box as frappe-ui's Breadcrumbs, so "Tickets" stays put between the list and a ticket. -->
  <div class="flex min-w-0 items-center leading-tighter">
    <span
      class="px-0.5 py-1 text-lg-medium leading-tighter text-ink-gray-5 shrink-0 max-sm:hidden"
      >{{ label }}</span
    >
    <span
      class="mx-0.5 text-base text-ink-gray-4 max-sm:hidden"
      aria-hidden="true"
      >/</span
    >
    <Dropdown v-model:open="isOpen" :options="options">
      <template #default="{ open }">
        <Button
          variant="ghost"
          class="min-w-0 max-w-[200px] !bg-transparent hover:!bg-surface-gray-3 focus-visible:!ring-0"
          :class="open && '!bg-surface-gray-3'"
        >
          <span class="text-lg-medium text-nowrap truncate">
            {{ currentView.label }}
          </span>
          <template #prefix>
            <ViewIcon :icon="currentView.icon" />
          </template>
          <template #suffix>
            <Icon
              :icon="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
              class="size-4 text-ink-gray-8"
            />
          </template>
        </Button>
      </template>

      <template #item-prefix="{ item }">
        <ViewIcon :icon="item.icon" />
      </template>

      <template #item-suffix="{ item }">
        <div
          v-if="item.name"
          class="flex items-center justify-end gap-2 min-w-11"
        >
          <Icon
            v-if="item.name === currentView.name"
            icon="lucide-check"
            class="size-4 text-ink-gray-7"
          />
          <!-- Always shown on touch, where no row is hovered. -->
          <Dropdown side="right" align="start" :options="closingActions(item)">
            <template #default="{ open }">
              <Button
                variant="ghost"
                class="ms-0 !size-4 rounded-1 [[data-slot=item][data-highlighted]_&]:!block [[data-slot=item][data-state=checked]_&]:!block [@media(hover:none)]:!block [@media(hover:none)]:!size-6"
                :class="open ? 'inline-flex' : 'hidden'"
                icon="lucide-more-horizontal"
                :aria-label="__('View actions')"
                @click.stop
              />
            </template>
          </Dropdown>
        </div>
      </template>
    </Dropdown>
  </div>
</template>

<script setup lang="ts">
import { h, ref } from "vue";
import { Button, Dropdown, Icon } from "frappe-ui";
import StoredIcon from "@helpdesk/shared/Icon.vue";
import { __ } from "@helpdesk/shared/translation";
import { isEmoji } from "@helpdesk/shared/utils";

const DEFAULT_ICON = "text-align-justify";
const ICON_CLASS = "size-4 shrink-0 text-ink-gray-7";

function ViewIcon(props: { icon?: string }) {
  const icon = props.icon || DEFAULT_ICON;
  const centre = isEmoji(icon) && "flex items-center justify-center leading-none";
  return h(StoredIcon, { icon, class: [ICON_CLASS, centre] });
}

// The header renders this only when a page hands it a view, so every prop arrives set.
const props = defineProps<{
  label: string;
  currentView: { name?: string; label: string; icon: string };
  options: any[];
  viewActions: (item: any) => any[];
}>();

const isOpen = ref(false);

// Popovers paint above dialogs, so the menu closes itself before an action opens one, as on the desk.
const closingActions = (item) =>
  props.viewActions(item).map((option) => ({
    ...option,
    onClick: () => {
      isOpen.value = false;
      option.onClick?.();
    },
  }));
</script>
