<template>
  <Dialog v-model="showSubjectDialog" :options="{ title: 'Rename Subject' }">
    <template #body-content>
      <div class="flex flex-col flex-1 gap-3">
        <FormControl
          v-model="renameSubject"
          type="textarea"
          size="sm"
          variant="subtle"
          :disabled="false"
        />
        <Button
          variant="solid"
          :loading="isLoading"
          label="Rename"
          @click="handleRename"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { TicketSymbol } from "@/types";
import { inject, ref } from "vue";

const ticket = inject(TicketSymbol);
const showSubjectDialog = defineModel();
const renameSubject = ref(ticket.value?.doc?.subject || "");
const isLoading = ref(false);

function handleRename() {
  isLoading.value = true;
  ticket.value.setValue.submit(
    {
      subject: renameSubject.value,
    },
    {
      onSuccess() {
        isLoading.value = false;
        showSubjectDialog.value = false;
      },
    }
  );
}
</script>

<style scoped></style>
