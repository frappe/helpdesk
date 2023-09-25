<template>
  <span>
    <LucideDot class="absolute -left-3 h-6 w-6 bg-white text-gray-500" />
    <div class="mb-1 font-medium text-gray-900 first-letter:capitalize">
      {{ user.name }} {{ action }}
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
import { UserInfo } from "@/types";

interface P {
  user: UserInfo;
  date: string;
  action?: string;
}

defineProps<P>();
</script>
