<template>
  <div
    v-if="showAlert && alertMessage"
    class="flex gap-4 justify-start p-4 bg-orange-50 text-orange-800 rounded-lg border border-orange-200"
  >
    <Clock class="size-5" />

    <div class="flex-1 flex flex-col gap-1 text-sm">
      <h4 class="font-semibold">Outside Business Hours</h4>
      <p>{{ alertMessage }}</p>
    </div>

    <button
      @click="dismissAlert"
      class="hover:text-orange-900"
      aria-label="Dismiss alert"
    >
      <X class="size-4" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { createResource } from "frappe-ui";
import { ref } from "vue";
import Clock from "~icons/lucide/clock";
import X from "~icons/lucide/x";

const showAlert = ref(false);
const alertMessage = ref("");
const isDismissed = ref(false);

const workingHours = createResource({
  url: "helpdesk.helpdesk.doctype.hd_settings.hd_settings.check_working_hours",
  auto: true,
  onSuccess: (data) => {
    if (data && data.show_message && !isDismissed.value) {
      showAlert.value = true;
      alertMessage.value = data.message;
    }
  },
  onError: (error) => {
    console.error("Error checking working hours:", error);
  },
});

function dismissAlert() {
  isDismissed.value = true;
  showAlert.value = false;
}

defineExpose({
  reload: () => workingHours.reload(),
});
</script>
