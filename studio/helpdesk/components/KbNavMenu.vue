<template>
  <Dropdown :options="options" :offset="4" placement="bottom-start">
    <template #default="{ open }">
      <button
        type="button"
        class="group flex cursor-pointer items-center gap-1 rounded-md bg-transparent p-0.5"
        aria-label="Menu"
      >
        <span class="kb-nav__logo size-8" />
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
import { Dropdown, FeatherIcon } from "frappe-ui";

defineProps<{ options?: unknown[] }>();
</script>

<style scoped>
/* Hardcoded product mark; being replaced by the site's own brand_logo from config. */
.kb-nav__logo {
  background-image: url("data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAxMTggMTE4IiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxwYXRoIGQ9Ik05My45Mjc4IDBIMjMuMTAxM0MxMC4zNDI4IDAgMCAxMC4zNDI4IDAgMjMuMTAxM1Y5My45Mjc4QzAgMTA2LjY4NiAxMC4zNDI4IDExNy4wMjkgMjMuMTAxMyAxMTcuMDI5SDkzLjkyNzhDMTA2LjY4NiAxMTcuMDI5IDExNy4wMjkgMTA2LjY4NiAxMTcuMDI5IDkzLjkyNzhWMjMuMTAxM0MxMTcuMDI5IDEwLjM0MjggMTA2LjY4NiAwIDkzLjkyNzggMFoiIGZpbGw9IiM3RDQyRkIiLz48cGF0aCBkPSJNOTUuOTc1OSA1MC44NzUzVjI3LjgyNjVMMjEgMjcuODI2NVYzOC4zMjcxSDg1LjUyNzhWNDguMzAyN0M4MS4zMjc1IDQ5LjUxMDMgNzguMjgyNCA1My4zOTU1IDc4LjI4MjQgNTcuOTYzMkM3OC4yODI0IDYyLjUzMSA4MS4zMjc1IDY2LjM2MzcgODUuNTI3OCA2Ny41NzEzVjc3LjU0NjhIMzEuNTAwNlY1MC4xNDAzSDIxVjg4LjA0NzRIOTYuMDI4NFY2NC45OTg2TDg5Ljc4MDUgNjAuNTM1OVY1NS4zOTA2TDk2LjAyODQgNTAuOTI3OEw5NS45NzU5IDUwLjg3NTNaIiBmaWxsPSIjRURGN0ZGIi8+PC9zdmc+");
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;
}
</style>
