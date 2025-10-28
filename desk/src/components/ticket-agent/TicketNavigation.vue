<template>
  <div class="flex gap-1">
    <Tooltip
      :text="
        getPreviousTicket()
          ? `Go to previous ticket: #${getPreviousTicket()}`
          : 'No previous ticket'
      "
      :disabled="disableLeftCondition"
    >
      <Button
        :icon="LucideChevronLeft"
        variant="ghost"
        :disabled="disableLeftCondition"
        @click="goToPreviousTicket()"
      />
    </Tooltip>
    <Tooltip
      :text="
        getNextTicket()
          ? `Go to next ticket: #${getNextTicket()}`
          : 'No next ticket'
      "
      :disabled="disableRightCondition"
    >
      <Button
        :icon="LucideChevronRight"
        variant="ghost"
        :disabled="disableRightCondition"
        @click="goToNextTicket()"
      />
    </Tooltip>
  </div>
</template>

<script setup lang="ts">
import { useShortcut } from "@/composables/shortcuts";
import {
  ticketsToNavigate,
  useTicketNavigation,
} from "@/composables/useTicketNavigation";
<<<<<<< HEAD
import { computed } from "vue";
=======
import { computed, onMounted, ref } from "vue";
>>>>>>> 8b1bd753 (fix: remove unwanted imports)
import LucideChevronLeft from "~icons/lucide/chevron-left";
import LucideChevronRight from "~icons/lucide/chevron-right";

const {
  currentTicketIndex,
  goToNextTicket,
  goToPreviousTicket,
  getNextTicket,
  getPreviousTicket,
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
</script>
