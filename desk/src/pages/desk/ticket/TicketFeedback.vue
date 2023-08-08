<template>
  <span>
    <div
      v-if="rating && feedback"
      class="flex items-center gap-1 border-b px-7 py-2 text-base"
      :class="{
        'cursor-pointer': !!extra,
        'hover:bg-gray-50': !!extra,
      }"
      @click="toggleDialog()"
    >
      <span class="flex items-center gap-1">
        <StarRating :rating="rating" />
        <Icon icon="lucide:dot" class="h-4 w-4 text-gray-600" />
        <span class="text-gray-800">
          {{ feedback }}
        </span>
      </span>
    </div>
    <Dialog v-model="showDialog" :options="{ title: 'Customer feedback' }">
      <template #body-content>
        <div class="space-y-4">
          <div class="flex items-center gap-2 text-gray-900">
            <StarRating :rating="rating" />
            <Icon icon="lucide:dot" class="h-4 w-4 text-gray-600" />
            <div class="text-base">
              {{ feedback }}
            </div>
          </div>
          <div class="text-base leading-relaxed">
            {{ extra }}
          </div>
        </div>
      </template>
    </Dialog>
  </span>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Dialog } from "frappe-ui";
import { Icon } from "@iconify/vue";
import StarRating from "@/components/StarRating.vue";
import { useTicket } from "./data";

const showDialog = ref(false);
const ticket = useTicket();
const rating = computed(() => ticket.value.data?.feedback?.rating);
const feedback = computed(() => ticket.value.data?.feedback?.label);
const extra = computed(() => ticket.value.data?.feedback_extra);

function toggleDialog() {
  if (!extra.value) return;
  showDialog.value = !showDialog.value;
}
</script>
