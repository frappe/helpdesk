<template>
  <div class="flex flex-col p-5">
    <ol class="relative text-base">
      <li v-for="event in history.data" :key="event.name" class="mb-4 ml-4">
        <TimelineItem :user="event.user" :date="event.creation">
          <template #main>
            <span class="flex flex-wrap gap-1 text-gray-900">
              <span class="font-medium">{{ event.user.name }}</span>
              <span class="text-gray-700">changed</span>
              <span class="font-medium">{{ event.value_change_field }}</span>
              <span class="text-gray-700">from</span>
              <span class="font-medium">{{ event.value_change_initial }}</span>
              <span class="text-gray-700">to</span>
              <span class="font-medium">{{ event.value_change_final }}</span>
            </span>
          </template>
        </TimelineItem>
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
const history = createListResource({
  doctype: 'HD Activity',
  fields: [
    'name',
    'creation',
    'user',
    'value_change_field',
    'value_change_final',
    'value_change_initial',
  ],
  filters: {
    reference_doctype: 'HD Ticket',
    reference_name: id,
    activity_type: 'Value change',
  },
  auto: true,
});
</script>
