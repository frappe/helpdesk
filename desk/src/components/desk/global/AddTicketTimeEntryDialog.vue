<template>
  <Dialog v-model="isVisible" :options="{ title: 'Complete Time Entry' }">
    <template #body-content>
      <div
        class="max-h-[73vh] min-h-[20rem] w-full max-w-full overflow-y-auto px-3"
      >
        <FormControl
          v-model="description"
          label="Description"
          type="textarea"
          placeholder="Describe your work..."
        />
        <p v-if="error" class="text-red-500">{{ error }}</p>
      </div>
      <div class="float-right space-x-2 text-right">
        <Button
          label="Submit"
          theme="gray"
          variant="solid"
          @click="submitDescription"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, defineEmits } from "vue";
import { Input, Dialog, ErrorMessage } from "frappe-ui";

const emit = defineEmits(["submit"]);
const isVisible = ref(false);
const description = ref("");
const error = ref("");

function submitDescription() {
  if (description.value.trim()) {
    emit("submit", description.value);
    description.value = ""; // Reset description after submit
    isVisible.value = false;
  } else {
    error.value = "Description cannot be empty.";
  }
}

// Expose showDialog method to be called from parent
defineExpose({ showDialog: () => (isVisible.value = true) });
</script>
