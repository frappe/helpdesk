<template>
  <Profile v-if="step === 'profile'" @updateStep="updateStep" />
  <UserEmailSettings
    v-else-if="step === 'user-email-settings'"
    @updateStep="updateStep"
  />
</template>
<script setup>
import Profile from "./Profile.vue";
import UserEmailSettings from "./UserEmailSettings.vue";
import { ref } from "vue";

const step = ref("profile");

function updateStep(newStep) {
  step.value = newStep;
}
</script>
