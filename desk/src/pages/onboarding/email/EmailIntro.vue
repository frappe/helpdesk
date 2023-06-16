<template>
  <div class="flex flex-col gap-4">
    <div class="text-gray-700">
      {{ help }}
    </div>
    <Button label="Let's go!" variant="outline" class="w-max" @click="next" />
  </div>
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";
import { useOnboardingEmailStore } from "./data";

const { next } = useOnboardingEmailStore();
const help =
  "Did you know that our Helpdesk becomes even more powerful when \
	integrated with email? With this integration, you can send and \
	receive emails directly from your Helpdesk inbox. It streamlines \
	communication and enhances productivity. Would you like assistance \
	in setting up your email integration now?";
</script>
