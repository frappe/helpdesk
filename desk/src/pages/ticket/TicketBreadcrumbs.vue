<template>
  <PageTitle>
    <template #title>
      <Breadcrumbs
        :items="[
          {
            label: __('Tickets'),
            route: {
              name: parent,
            },
          },
          {
            label: ticket?.data?.subject || title,
            route: {
              name: current,
            },
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
import { Breadcrumbs } from "frappe-ui";
import { PageTitle } from "@/components";
import { __ } from "@/translation";
import { ITicket } from "./symbols";

interface P {
  parent: string;
  current: string;
  title?: string;
}

withDefaults(defineProps<P>(), {
  title: "",
});
const ticket = inject(ITicket);
</script>
