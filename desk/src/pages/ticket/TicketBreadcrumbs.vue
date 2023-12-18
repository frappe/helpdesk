<template>
  <PageTitle>
    <template #title>
      <BreadCrumbs
        :items="[
          {
            label: 'Tickets',
            route: {
              name: parent,
            },
          },
          {
            label: ticket?.data?.subject || title,
            name: ticket?.data?.name,
          },
        ]"
      />
    </template>
    <template #right>
      <slot name="right" />
    </template>
  </PageTitle>
</template>

<script setup lang="ts">
import { inject } from "vue";
import { BreadCrumbs, PageTitle } from "@/components";
import { ITicket } from "./symbols";

interface P {
  parent: string;
  title?: string;
}

withDefaults(defineProps<P>(), {
  title: "",
});
const ticket = inject(ITicket);
</script>
