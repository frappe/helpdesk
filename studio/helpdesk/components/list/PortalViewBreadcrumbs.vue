<template>
  <div class="flex items-center">
    <span class="pe-0.5 py-1 text-lg-medium text-ink-gray-5">{{ label }}</span>
    <span class="ml-0.5 text-base text-ink-gray-4" aria-hidden="true"> / </span>
    <Dropdown :options="options">
      <template #default="{ open }">
        <Button
          variant="ghost"
          class="max-w-[200px] sm:max-w-none !bg-transparent hover:!bg-surface-gray-3 focus-visible:!ring-0"
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
          <Dropdown side="right" align="start" :options="viewActions(item)">
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
import { h } from "vue";
import { Button, Dropdown, Icon } from "frappe-ui";
import { Icon as SpriteIcon } from "frappe-ui/experimental";
import { __ } from "@helpdesk/shared/translation";
import { isEmoji } from "@helpdesk/shared/utils";

const DEFAULT_ICON = "text-align-justify";
const ICON_CLASS = "size-4 shrink-0 text-ink-gray-7";

// The sprite, not a mask class: a stored name may be one the build never saw.
function ViewIcon(props: { icon?: string }) {
  const icon = props.icon || DEFAULT_ICON;
  if (isEmoji(icon))
    return h(
      "div",
      { class: [ICON_CLASS, "flex items-center justify-center leading-none"] },
      icon
    );
  return h(SpriteIcon, {
    name: icon.replace(/^lucide-/, ""),
    class: ICON_CLASS,
  });
}

// The header renders this only when a page hands it a view, so every prop arrives set.
defineProps<{
  label: string;
  currentView: { name?: string; label: string; icon: string };
  options: any[];
  viewActions: (item: any) => any[];
}>();
</script>
