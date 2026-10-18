<template>
  <Dropdown v-if="options?.length" :options="options" :offset="4" align="start">
    <template #default="{ open }">
      <button
        type="button"
        :aria-label="name"
        class="-ms-2 flex h-8 min-w-0 max-w-[15rem] shrink-0 cursor-pointer items-center gap-2 rounded-5 px-2 transition-colors duration-300 ease-in-out"
        :class="open ? 'bg-surface-gray-3' : 'hover:bg-surface-gray-3'"
      >
        <Brand />
        <Icon
          icon="lucide-chevron-down"
          class="size-4 shrink-0 text-ink-gray-5 transition-transform duration-200"
          :class="{ 'rotate-180': open }"
        />
      </button>
    </template>
  </Dropdown>
  <RouterLink
    v-else
    :to="ROUTES.home"
    :aria-label="name"
    class="flex h-8 min-w-0 max-w-[15rem] shrink-0 items-center gap-2"
  >
    <Brand />
  </RouterLink>
</template>

<script setup lang="ts">
import { computed, h } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { Dropdown, Icon } from "frappe-ui";
import { ROUTES } from "@helpdesk/shared/portalRoutes";

const props = defineProps<{
  options?: unknown[];
  logo?: string;
  name?: string;
}>();

const route = useRoute();
const isTicketPage = computed(
  () =>
    route.path === ROUTES.ticketList || route.path.startsWith(ROUTES.ticket(""))
);

function Brand() {
  return [
    props.logo
      ? h("img", {
          src: props.logo,
          alt: "",
          "aria-hidden": "true",
          class: "size-6 shrink-0 rounded-2 object-contain",
        })
      : h("span", { class: "size-6 shrink-0" }),
    !isTicketPage.value &&
      h(
        "span",
        {
          class: "hidden truncate text-base-medium text-ink-gray-9 sm:block",
        },
        props.name
      ),
  ];
}
</script>
