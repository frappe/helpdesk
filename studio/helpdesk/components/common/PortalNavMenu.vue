<template>
  <Dropdown v-if="options?.length" :options="options" :offset="4" align="start">
    <template #default="{ open }">
      <button
        type="button"
        class="group flex cursor-pointer items-center gap-1 rounded-5 bg-transparent p-0.5"
        :aria-label="__('Menu')"
      >
        <Logo />
        <Icon
          :icon="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
          class="size-4 shrink-0 transition-colors duration-150 group-hover:text-ink-gray-9"
          :class="open ? 'text-ink-gray-9' : 'text-ink-gray-5'"
        />
      </button>
    </template>
  </Dropdown>
  <RouterLink
    v-else
    :to="ROUTES.home"
    class="flex rounded-5 p-0.5"
    :aria-label="__('Knowledge base')"
  >
    <Logo />
  </RouterLink>
</template>

<script setup lang="ts">
import { h } from "vue";
import { RouterLink } from "vue-router";
import { Dropdown, Icon } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import { ROUTES } from "@app/routes";

const props = defineProps<{ options?: unknown[]; logo?: string }>();

function Logo() {
  return props.logo
    ? h("img", {
        src: props.logo,
        alt: "",
        "aria-hidden": "true",
        class: "size-8 shrink-0 object-contain",
      })
    : h("span", { class: "size-8 shrink-0" });
}
</script>
