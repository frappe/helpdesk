<template>
  <div v-if="!isEmpty(fields)" class="flex flex-col gap-5 border-b py-4">
    <div v-for="field in fields" :key="field.label">
      <div v-if="field.value" class="flex flex-col gap-2.5">
        <div class="text-base text-gray-600">{{ field.label }}</div>
        <a :href="field.route || null" target="_blank">
          <div class="flex items-center gap-2">
            <div class="flex h-4 w-4 items-center justify-center">
              <IconLink v-if="field.route" class="h-5 w-5 text-gray-600" />
              <IconLayer v-else class="h-4 w-4 text-gray-600" />
            </div>
            <div class="text-base text-gray-800">{{ field.value }}</div>
          </div>
        </a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { isEmpty } from "lodash";
import { computed } from "vue";
import { useTicketStore } from "./data";
import IconLayer from "~icons/lucide/layers";
import IconLink from "~icons/lucide/external-link";

const { ticket } = useTicketStore();
const fields = computed(() => ticket.doc?.custom_fields);
</script>
