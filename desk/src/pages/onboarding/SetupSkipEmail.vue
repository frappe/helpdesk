<template>
  <div class="flex flex-col gap-4 text-gray-800">
    {{ query }}
    <Button
      :label="isYes ? 'No' : 'Yes'"
      class="w-max"
      variant="outline"
      @click="update(!isYes)"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { createResource, Button } from "frappe-ui";
import { capture } from "@/telemetry";

const query =
  "Did you know that our Helpdesk is designed to function independently, \
	without relying on email? Our customer portal is finely tuned to be a \
	standalone solution, eliminating the hassle of email setup. Would you \
	like me to disable the email workflow for you?";
const isYes = ref(false);

const r = createResource({
  url: "frappe.client.set_value",
  debounce: 1000,
  onSuccess(data) {
    isYes.value = data.skip_email_workflow;
    const cond = isYes.value ? "yes" : "no";
    const event = "onboarding_skip_email_" + cond;
    capture(event);
  },
});

function update(value: boolean) {
  r.submit({
    doctype: "HD Settings",
    name: "HD Settings",
    fieldname: "skip_email_workflow",
    value,
  });
}

onMounted(() => capture("onboarding_skip_email_reached"));
</script>
