<template>
  <div v-if="!isEmpty(fields)" class="flex flex-col gap-5 border-b py-4">
    <div v-for="field in fields" :key="field.label">
      <div v-if="ticket.data[field.fieldname]" class="flex flex-col gap-2.5">
        <div class="text-base text-gray-600">{{ field.label }}</div>
        <a :href="getUrl(ticket.data[field.fieldname])" target="_blank">
          <div class="flex items-center gap-2">
            <div class="flex h-4 w-4 items-center justify-center">
              <Icon
                :icon="
                  getUrl(ticket.data[field.fieldname])
                    ? 'lucide:external-link'
                    : 'lucide:disc'
                "
                class="h-4 w-4 text-gray-600"
              />
            </div>
            <div class="text-base text-gray-800">
              {{ getValue(field) }}
            </div>
          </div>
        </a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { isEmpty } from "lodash";
import zod from "zod";
import { Icon } from "@iconify/vue";
import { Field } from "@/types";
import { useTicket } from "./data";

const ticket = useTicket();
const fields = computed(() => ticket.value.data.template.fields);

function getUrl(url: string) {
  const isUrl = zod.string().url().safeParse(url).success;
  return isUrl ? url : null;
}

function getValue(field: Field) {
  const v = ticket.value.data[field.fieldname];
  if (field.fieldtype === "Check") {
    return v ? "Yes" : "No";
  }
  return v;
}
</script>
