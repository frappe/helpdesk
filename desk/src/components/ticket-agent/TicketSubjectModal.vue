<template>
  <Dialog v-model="showSubjectDialog" :options="{ title: 'Rename Subject' }">
    <template #body-content>
      <div class="flex flex-col flex-1 gap-3">
        <FormControl
          ref="subjectInput"
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
          :disabled="renameSubject === ticket?.doc?.subject"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { TicketSymbol } from "@/types";
import { inject, ref, watch, nextTick } from "vue";
const ticket = inject(TicketSymbol);
const showSubjectDialog = defineModel<boolean>({ default: false });
const renameSubject = ref(ticket.value?.doc?.subject || "");
const isLoading = ref(false);
const subjectInput = ref<any>(null);

watch(
  () => showSubjectDialog.value,
  async (val) => {
    if (val) {
      await nextTick();
      subjectInput.value?.$el?.querySelector("textarea").focus();
    }
  }
);

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
