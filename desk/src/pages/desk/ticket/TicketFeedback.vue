<template>
  <span>
    <div
      v-if="rating && feedback"
      class="flex cursor-pointer items-center gap-2 border-b px-7 py-3 text-base hover:bg-gray-50"
      @click="showDialog = !showDialog"
    >
      <StarRating :rating="rating" />
      <span class="line-clamp-1">
        {{ feedback }}
      </span>
    </div>
    <Dialog v-model="showDialog" :options="{ title: 'Customer feedback' }">
      <template #body-content>
        <div class="space-y-4">
          <StarRating :rating="rating" />
          <div class="text-base leading-relaxed">
            {{ feedback }}
          </div>
        </div>
      </template>
    </Dialog>
  </span>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Dialog } from "frappe-ui";
import StarRating from "@/components/StarRating.vue";
import { useTicket } from "./data";

const showDialog = ref(false);
const ticket = useTicket();
const rating = computed(() => ticket.value.data?.satisfaction_rating);
const feedback = computed(() => ticket.value.data?.customer_feedback);
</script>
