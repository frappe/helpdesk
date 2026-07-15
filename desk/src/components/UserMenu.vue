<template>
  <Dropdown :options="options">
    <template #default="{ open }">
      <button
        class="flex h-12 items-center rounded-md py-2 duration-300 ease-in-out"
        :class="
          collapsed
            ? 'w-auto px-0'
            : open
            ? 'w-full px-2 bg-surface-base shadow-sm'
            : 'w-full px-2 hover:bg-surface-gray-3'
        "
      >
        <BrandLogo />
        <div
          class="flex flex-1 flex-col text-left duration-300 ease-in-out overflow-hidden"
          :class="
<<<<<<< HEAD
            !sidebarStore.isExpanded
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 w-auto opacity-100'
=======
            collapsed
              ? 'ms-0 w-0 overflow-hidden opacity-0'
              : 'ms-2 w-auto opacity-100'
>>>>>>> 8fa03b64 (fix(views): use icons instead of emojis)
          "
        >
          <div class="text-base-medium leading-none text-ink-gray-9 truncate">
            {{ config.brandName || "Helpdesk" }}
          </div>
          <div class="mt-1 text-sm text-ink-gray-7">
            {{ authStore.userName }}
          </div>
        </div>
        <div
          class="duration-300 ease-in-out"
          :class="
<<<<<<< HEAD
            !sidebarStore.isExpanded
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 relative left-[-2.5px] w-auto opacity-100'
=======
            collapsed
              ? 'ms-0 w-0 overflow-hidden opacity-0'
              : 'ms-2 relative start-[-2.5px] w-auto opacity-100'
>>>>>>> 8fa03b64 (fix(views): use icons instead of emojis)
          "
        >
          <FeatherIcon
            name="chevron-down"
            class="h-4 w-4 text-ink-gray-5"
            aria-hidden="true"
          />
        </div>
      </button>
    </template>
  </Dropdown>
</template>

<script setup lang="ts">
import BrandLogo from "@/components/BrandLogo.vue";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { useSidebarStore } from "@/stores/sidebar";
import { Dropdown } from "frappe-ui";
import { computed } from "vue";

const config = useConfigStore();

const props = defineProps({
  options: {
    type: Array,
    required: true,
  },
  isCollapsed: {
    type: Boolean,
    default: null,
  },
});

const authStore = useAuthStore();
const sidebarStore = useSidebarStore();

const collapsed = computed(() => props.isCollapsed ?? !sidebarStore.isExpanded);
</script>
