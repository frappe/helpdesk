<template>
  <div class="flex gap-1">
    <Button
      :icon="LucideChevronLeft"
      variant="ghost"
      :disabled="disableLeftCondition"
      @click="goToPreviousTicket()"
    />
    <Button
      :icon="LucideChevronRight"
      variant="ghost"
      :disabled="disableRightCondition"
      @click="goToNextTicket()"
    />
  </div>
</template>

<script setup lang="ts">
import {
  ticketsToNavigate,
  useTicketNavigation,
} from "@/composables/useTicketNavigation";
import { computed } from "vue";
import LucideChevronLeft from "~icons/lucide/chevron-left";
import LucideChevronRight from "~icons/lucide/chevron-right";

const { currentTicketIndex, goToNextTicket, goToPreviousTicket } =
  useTicketNavigation();

const disableLeftCondition = computed(() => {
  if (ticketsToNavigate.loading || !ticketsToNavigate.data?.length) return true;

  return currentTicketIndex.value == 0;
});

const disableRightCondition = computed(() => {
  if (ticketsToNavigate.loading || !ticketsToNavigate.data?.length) return true;
  if (ticketsToNavigate.data.length <= 1) return true;
  return currentTicketIndex.value >= ticketsToNavigate.data.length - 1;
});
</script>
