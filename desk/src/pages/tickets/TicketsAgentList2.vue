<template>
<ListView
  class="h-[250px]"
  :columns = columns
  :rows = rows
  :options="{
    getRowRoute: (row) => ({ name: 'TicketAgent', params: { ticketId: row.name } }),
    selectable: true,
    showTooltip: true,
  }"
  row-key="id"
/>
</template>

<script setup lang="ts">
import { ListView } from 'frappe-ui';

defineProps({
  columns: {
    type: Array, //TODO custom types
    required: true,
  },
  rows: {
    type: Array,
    required: true,
  },
});

</script>