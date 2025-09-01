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
import { useTicketNavigation } from "@/composables/useTicketNavigation";
import { computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import LucideChevronLeft from "~icons/lucide/chevron-left";
import LucideChevronRight from "~icons/lucide/chevron-right";

const route = useRoute();

const {
  currentTicketIndex,
  ticketsToNavigate,
  goToNextTicket,
  goToPreviousTicket,
  getCurrentTicket,
} = useTicketNavigation();

const disableLeftCondition = computed(() => {
  if (ticketsToNavigate.loading || !ticketsToNavigate.data?.length) return true;

  return currentTicketIndex.value == 0;
});

const disableRightCondition = computed(() => {
  if (ticketsToNavigate.loading || !ticketsToNavigate.data?.length) return true;
  if (ticketsToNavigate.data.length <= 1) return true;
  return currentTicketIndex.value >= ticketsToNavigate.data.length - 1;
});

onMounted(() => {
  ticketsToNavigate.update({
    params: {
      ticket: route.params.ticketId as string,
      current_view: route.query.view as string,
    },
  });

  ticketsToNavigate.reload();
});
</script>
