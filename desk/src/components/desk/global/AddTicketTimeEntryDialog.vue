<template>
  <Dialog v-model="isVisible" :options="{ title: 'Complete Time Entry' }">
    <template #body-content>
      <div class="p-2">
        <div class="space-y-1">
          <label for="duration" class="block text-sm font-medium text-gray-700">Duration</label>
          <div class="mt-1 flex">
            <input
              type="text"
              id="duration"
              @blur="validateTime"
              v-model="formattedInput"
              maxlength="8"
              class="border-gray-400 placeholder-gray-500 form-input block w-half"
            />
          </div>
          <ErrorMessage :message="validationError" />
        </div>
      </div>
      <div class="p-2">
        <div class="space-y-1">
          <label for="description" class="block text-sm font-medium text-gray-700">Description</label>
          <FormControl
            v-model="description"
            type="textarea"
            placeholder="Describe your work..."
            rows="10"
            class="mt-1 flex border-gray-400"
          />
          <p v-if="error" class="text-red-500">{{ error }}</p>
        </div>
      </div>
      <div class="float-right space-x-2 text-right">
        <Button
          label="Submit"
          theme="gray"
          variant="solid"
          @click="submitdialog"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, defineProps, defineEmits, computed } from "vue";
import { Dialog, ErrorMessage } from "frappe-ui";

const props = defineProps({
  elapsedTimeInitial: String
});
const emit = defineEmits(["submit"]);
const isVisible = ref(false);
const description = ref("");
const error = ref("");
const rawInput = ref(props.elapsedTimeInitial);
const validationError = ref('');

const showDialog = () => {
  isVisible.value = true;
};

// Function to update elapsed time initial directly
const updateElapsedTimeInitial = (newElapsedTime) => {
  rawInput.value = newElapsedTime;
  console.log("Updated elapsed time initial to:", newElapsedTime);
};

function submitdialog() {
  console.log('rawInput.value is: '+rawInput.value)
  emit("submit", { description: description.value, elapsedtime: rawInput.value });
  description.value = ""; // Reset description after submit
  isVisible.value = false;
}

const formattedInput = computed({
  get() {
    return rawInput.value;
  },
  set(value) {
    const numbers = value.replace(/\D/g, ''); // Remove all non-digit characters
    let formatted = '';

    if (numbers.length <= 2) {
      // Up to two digits: directly use them as hours
      formatted = numbers;
    } else if (numbers.length <= 4) {
      // More than two digits, but less than or equal to four digits: insert a colon between hours and minutes
      formatted = numbers.slice(0, 2) + ':' + numbers.slice(2, 4);
    } else {
      // More than four digits: insert colons between hours, minutes, and seconds
      formatted = numbers.slice(0, 2) + ':' + numbers.slice(2, 4) + ':' + numbers.slice(4, 6);
    }

    // Update the rawInput value with the formatted string
    rawInput.value = formatted;
  }
});

function validateTime() {
  console.log('formattedInput is: '+formattedInput.value)
  const regex = /^([0-1]?[0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])$/;
  if (regex.test(formattedInput.value)) {
    validationError.value = '';
    // Proceed with submitting or processing the valid time
    // For example, convert to milliseconds or any other operation
  } else {
    validationError.value = 'Please enter a valid time in HH:MM:SS format.';
    // Handle invalid time format
  }
}

// Expose showDialog method to be called from parent
defineExpose({ showDialog, updateElapsedTimeInitial });
</script>

<style>
.error {
  color: red;
}
</style>