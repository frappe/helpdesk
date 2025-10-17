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
import {
  ticketsToNavigate,
  useTicketNavigation,
} from "@/composables/useTicketNavigation";
import { useShortcut } from "@/composables/shortcuts";
import { computed, onMounted, onUnmounted, ref } from "vue";
import LucideChevronLeft from "~icons/lucide/chevron-left";
import LucideChevronRight from "~icons/lucide/chevron-right";

const {
  currentTicketIndex,
  goToNextTicket,
  goToPreviousTicket,
  getNextTicket,
  getPreviousTicket,
} = useTicketNavigation();

const leftArrowRef = ref(null);
const rightArrowRef = ref(null);

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
  // Register shortcuts and store cleanup functions
  useShortcut({ key: ">", shift: true }, () => {
    if (!disableRightCondition.value) {
      goToNextTicket();
    }
  });

  useShortcut({ key: "<", shift: true }, () => {
    if (!disableLeftCondition.value) {
      goToPreviousTicket();
    }
  });
});
</script>
