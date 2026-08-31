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
            <FeatherIcon
              :name="open ? 'chevron-up' : 'chevron-down'"
              class="h-4 text-ink-gray-8"
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
          <FeatherIcon
            v-if="item.name === currentView.name"
            name="check"
            class="size-4 text-ink-gray-7"
          />
          <Dropdown side="right" align="start" :options="viewActions(item)">
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

<script setup lang="ts">
// The portal's list-view breadcrumb: `Tickets / <view> v`. Mirrors the agent desk's
// `desk/src/components/ViewBreadcrumbs.vue` markup so both list views read as one
// design. View icons come from the lucide sprite (see ViewIcon); the fixed chevron and
// check stay on FeatherIcon, whose glyphs are bundled regardless.
import { h } from "vue";
import { Button, Dropdown, FeatherIcon } from "frappe-ui";

// A view's stored icon is usually an emoji (that is what the desk's IconPicker writes),
// occasionally an icon name, often nothing. Mirrors `getIcon` in desk/src/utils.ts:
// emoji render as text, a name resolves against the sprite, and an empty one falls back
// to the list glyph rather than an empty slot.
const ICON_CLASS = "size-4 shrink-0 text-ink-gray-7";
// lucide names this glyph `text-align-justify`; `align-justify` is not in the sprite.
const DEFAULT_ICON = "text-align-justify";
const isEmoji = (value: string) => /\p{Extended_Pictographic}/u.test(value);

const ViewIcon = (props: { icon?: string }) => {
  const icon = props.icon;
  if (icon && isEmoji(icon))
    return h(
      "div",
      { class: `${ICON_CLASS} flex items-center justify-center leading-none` },
      icon
    );
  // Referenced straight out of the lucide sprite the renderer injects, rather than
  // FeatherIcon: IconPicker writes lucide names, and the two sets don't overlap
  // cleanly — a picked icon rendered as feather would come back empty.
  // Sprite symbols carry only paths, so the consuming svg supplies lucide's own
  // stroke defaults — without them the glyph renders as nothing.
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
};

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

<style>
[data-slot="item"][data-highlighted] .kebab-btn,
[data-slot="item"][data-state="checked"] .kebab-btn {
  display: block;
}
</style>
