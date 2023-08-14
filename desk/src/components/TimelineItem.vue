<template>
  <span>
    <Icon
      icon="lucide:dot"
      class="absolute -left-3 h-6 w-6 bg-white text-gray-500"
    />
    <div class="mb-1 font-medium text-gray-900 first-letter:capitalize">
      {{ user?.full_name || user }} {{ action }}
    </div>
    <Tooltip :text="dayjs(date).long()">
      <div class="text-gray-700 first-letter:capitalize">
        {{ dayjs(date).fromNow() }}
      </div>
    </Tooltip>
  </span>
</template>

<script setup lang="ts">
import { Tooltip } from "frappe-ui";
import { dayjs } from "@/dayjs";
import { Icon } from "@iconify/vue";
import { useUserStore } from "@/stores/user";

interface P {
  user: string;
  date: string;
  action?: string;
}

const props = withDefaults(defineProps<P>(), {
  action: "",
});
const userStore = useUserStore();
const user = userStore.getUser(props.user);
</script>
