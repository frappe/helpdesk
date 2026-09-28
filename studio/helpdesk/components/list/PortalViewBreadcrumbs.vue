<template>
  <div class="flex items-center">
    <button
      class="ps-0 pe-0.5 py-1 text-lg-medium text-ink-gray-5 hover:text-ink-gray-7 flex items-center justify-center focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
      @click="emit('parentClick')"
    >
      {{ label }}
    </button>
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
          <Dropdown side="right" align="start" :options="viewActions(item)">
            <template #default="{ open }">
              <Button
                variant="ghost"
                class="ms-0 !size-4 rounded-1 [[data-slot=item][data-highlighted]_&]:!block [[data-slot=item][data-state=checked]_&]:!block"
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

<script setup lang="ts">
// View icons come from the lucide sprite; the fixed chevron and check use Icon.
import { h } from "vue";
import { Button, Dropdown, Icon } from "frappe-ui";
import { isEmoji } from "@helpdesk/shared/utils";

// A stored icon is usually an emoji, occasionally a name, often nothing.
const ICON_CLASS = "size-4 shrink-0 text-ink-gray-7";
// lucide names this glyph `text-align-justify`; `align-justify` is not in the sprite.
const DEFAULT_ICON = "text-align-justify";

function ViewIcon(props: { icon?: string }) {
  const icon = props.icon;
  if (icon && isEmoji(icon))
    return h(
      "div",
      { class: [ICON_CLASS, "flex items-center justify-center leading-none"] },
      icon
    );
  // The sprite, not Icon: a stored name may be one the mask plugin never saw at build time.
  // Sprite symbols carry only paths, so the svg has to supply lucide's stroke defaults.
  const name = (icon || DEFAULT_ICON).replace(/^lucide-/, "");
  return h(
    "svg",
    {
      class: ICON_CLASS,
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      "stroke-width": 2,
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
      "aria-hidden": "true",
    },
    [h("use", { href: `#${name}` })]
  );
}

withDefaults(
  defineProps<{
    label?: string;
    currentView?: { name?: string; label: string; icon: string };
    options?: any[];
    viewActions?: (item: any) => any[];
  }>(),
  {
    label: "Tickets",
    currentView: () => ({ label: "List", icon: DEFAULT_ICON }),
    options: () => [],
    viewActions: () => () => [],
  }
);

const emit = defineEmits<{ (e: "parentClick"): void }>();
</script>
