<template>
  <Dropdown :options="options" :offset="4" placement="bottom-start">
    <template #default="{ open }">
      <button
        type="button"
        class="group flex cursor-pointer items-center gap-1 rounded-md bg-transparent p-0.5"
        aria-label="Menu"
      >
        <img
          v-if="logo"
          :src="logo"
          alt=""
          aria-hidden="true"
          class="size-8 shrink-0 object-contain"
        />
        <span v-else class="size-8 shrink-0" />
        <FeatherIcon
          :name="open ? 'chevron-up' : 'chevron-down'"
          class="size-4 shrink-0 transition-colors duration-150 group-hover:text-ink-gray-9"
          :class="open ? 'text-ink-gray-9' : 'text-ink-gray-5'"
        />
      </button>
    </template>
  </Dropdown>
</template>

<script setup lang="ts">
// The topbar's account menu, trigger and all. Was three Studio blocks — a Dropdown whose
// `open` prop was a hardcoded `false` — which left the chevron pointing down while the
// menu stood open and the trigger dead to the touch. A trigger has to read its own menu's
// state, and only the slot knows it, so this owns both.
//
// The chevron alone answers: it darkens under the pointer and flips while the menu is
// open. No fill behind the mark — the logo is the brand, and a grey slab around it every
// time the pointer passes reads as a button the mark was never meant to be.
import { computed } from "vue";
import { Dropdown, FeatherIcon } from "frappe-ui";
import { useSession } from "@app/stores/session";

defineProps<{ options?: unknown[] }>();

// The site's own mark, exactly as HD Settings brands it — the favicon is what the
// helpdesk falls back to everywhere else, so the topbar falls back with it.
const { config } = useSession();
const logo = computed(
  () => config.value?.brand_logo || config.value?.favicon || ""
);
</script>
