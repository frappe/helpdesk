<template>
  <Dialog v-model="isVisible" :options="{ title: 'Complete Time Entry' }">
    <template #body-content>
      <div class="p-2">
        <div class="space-y-1">
          <label for="duration" class="block text-sm font-medium text-gray-700"
            >Duration</label
          >
          <div class="mt-1 flex">
            <input
              id="duration"
              v-model="formattedInput"
              type="text"
              maxlength="8"
              class="form-input w-half block border-gray-400 placeholder:text-gray-500"
              @input="handleTimeInput($event.target.value)"
              @blur="validateTime(formattedInput)"
            />
          </div>
          <ErrorMessage :message="validationError" />
        </div>
      </div>
      <div class="p-2">
        <div class="space-y-1">
          <label
            for="description"
            class="block text-sm font-medium text-gray-700"
            >Description</label
          >
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
import { ref, defineEmits } from "vue";
import { Dialog, ErrorMessage } from "frappe-ui";

const emit = defineEmits(["submit"]);
const isVisible = ref(false);
const description = ref("");
const error = ref("");
const validationError = ref("");
const formattedInput = ref("");
let originalElapsedTime;

function showDialog(elapsedTime) {
  formattedInput.value = originalElapsedTime = convertMsToTime(elapsedTime);
  isVisible.value = true;
}

// Convert milliseconds to HH:MM:SS format
const convertMsToTime = (ms) => {
  let seconds = Math.floor((ms / 1000) % 60),
    minutes = Math.floor((ms / (1000 * 60)) % 60),
    hours = Math.floor(ms / (1000 * 60 * 60));

  seconds = String(seconds).padStart(2, "0");
  minutes = String(minutes).padStart(2, "0");
  hours = String(hours).padStart(2, "0");

  return `${hours}:${minutes}:${seconds}`;
};

// Convert HH:MM:SS format back to milliseconds
const convertTimeToMs = (time) => {
  const [hours, minutes, seconds] = time.split(":").map(Number);
  return (hours * 3600 + minutes * 60 + seconds) * 1000;
};

function submitdialog() {
  if (validateTime(formattedInput.value)) {
    const finalElapsedTimeMs = convertTimeToMs(formattedInput.value);
    const hasOverride = formattedInput.value !== originalElapsedTime;
    emit("submit", {
      description: description.value,
      elapsedtime: finalElapsedTimeMs,
      override_duration: hasOverride ? finalElapsedTimeMs : undefined, // Only send override if there's a change
    });
    description.value = ""; // Reset description after submit
    isVisible.value = false;
  }
}

function validateTime(time) {
  const regex = /^([0-1]?[0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])$/;
  const isValidFormat = regex.test(time);
  const isNonZeroDuration = time !== "00:00:00";

  if (!isValidFormat) {
    validationError.value = "Please enter a valid time in HH:MM:SS format.";
  } else if (!isNonZeroDuration) {
    validationError.value = "Duration cannot be 0 seconds.";
  } else {
    validationError.value = "";
  }

  return isValidFormat && isNonZeroDuration;
}

const handleTimeInput = (value) => {
  formattedInput.value = formatTimeInput(value);
};

const formatTimeInput = (time) => {
  const formattedTime = time
    .replace(/\D/g, "")
    .replace(/(\d{2})(?=\d)/g, "$1:");
  return formattedTime.substring(0, 8);
};

// Expose showDialog method to be called from parent
defineExpose({ showDialog });
</script>

<style>
.error {
  color: red;
}
</style>
