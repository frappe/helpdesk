<template>
  <!-- <div
    v-if="ticketsToNavigate.data?.length > 1"
    class="flex gap-1 rtl:flex-row-reverse"
  >
    <Tooltip
      :text="
        getPreviousTicket()
          ? __(`Go to previous ticket (Shift + <)`)
          : __('No previous ticket')
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
          ? __(`Go to next ticket (Shift + >)`)
          : __('No next ticket')
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
  </div> -->
</template>

<script setup lang="ts">
import { useShortcut } from "@/composables/shortcuts";
import {
  ticketsToNavigate,
  useTicketNavigation,
} from "@/composables/useTicketNavigation";
import { computed, onMounted } from "vue";

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
