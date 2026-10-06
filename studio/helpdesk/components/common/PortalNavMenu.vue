<template>
  <Dropdown v-if="options?.length" :options="options" :offset="4" align="start">
    <template #default="{ open }">
      <button
        type="button"
        :class="[BUTTON, open ? 'bg-surface-gray-3' : 'bg-surface-gray-2']"
      >
        <Brand />
        <Icon
          :icon="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
          class="size-4 shrink-0 text-ink-gray-5"
        />
      </button>
    </template>
  </Dropdown>
  <RouterLink v-else :to="ROUTES.home" :class="[BUTTON, 'bg-surface-gray-2']">
    <Brand />
  </RouterLink>
</template>

<script setup lang="ts">
import { h } from "vue";
import { RouterLink } from "vue-router";
import { Dropdown, Icon } from "frappe-ui";
import { ROUTES } from "@app/routes";

const props = defineProps<{
  options?: unknown[];
  logo?: string;
  name?: string;
}>();

const BUTTON =
  "flex h-9 min-w-0 max-w-64 cursor-pointer items-center gap-2 rounded-lg pe-2 ps-1.5 transition-colors hover:bg-surface-gray-3";

function Brand() {
  return [
    props.logo &&
      h("img", {
        src: props.logo,
        alt: "",
        "aria-hidden": "true",
        class: "size-6 shrink-0 rounded-md object-contain",
      }),
    h(
      "span",
      { class: "truncate text-base font-medium text-ink-gray-8" },
      props.name
    ),
  ];
}
</script>
