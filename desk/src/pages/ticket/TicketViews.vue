<template>
  <div class="flex flex-col p-5">
    <ol class="relative text-base">
      <li v-for="event in views.data" :key="event.name" class="mb-4 ml-4">
        <TimelineItem :user="event.user" :date="event.last_visit" />
      </li>
    </ol>
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue';
import { createListResource } from 'frappe-ui';
import { TimelineItem } from '@/components';
import { Id } from './symbols';

const id = inject(Id);
const views = createListResource({
  doctype: 'HD Visit',
  fields: ['name', 'user', 'last_visit'],
  filters: {
    reference_doctype: 'HD Ticket',
    reference_name: id,
  },
  auto: true,
});
</script>
