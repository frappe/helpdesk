<template>
  <Resizer class="flex flex-col border-l h-full" side="right">
    <TicketDetailsTab />
  </Resizer>
</template>

<script setup lang="ts">
import Resizer from "../Resizer.vue";
import TicketDetailsTab from "./TicketDetailsTab.vue";
</script>
