<template>
  <span>
    <div class="flex justify-between px-6 pt-6 pb-2">
      <div class="text-2xl font-semibold text-gray-900">Tickets</div>
      <Button
        icon-left="plus"
        label="New ticket"
        class="bg-gray-900 text-white hover:bg-gray-800"
        @click="isDialogVisible = true"
      />
    </div>
    <NewTicketDialog
      v-model="isDialogVisible"
      @close="isDialogVisible = false"
    />
  </span>
</template>

<script setup lang="ts">
import { ref } from "vue";
import NewTicketDialog from "./NewTicketDialog.vue";

const isDialogVisible = ref(false);
</script>
