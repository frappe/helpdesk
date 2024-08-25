<template>
  <div class="flex-1">
    <div v-if="step === 'email-list'" class="h-full">
      <EmailAccountList />
    </div>
    <div v-else-if="step === 'email-add'" class="h-full">
      <EmailAdd />
    </div>
    <div v-else-if="step === 'email-edit'" class="h-full">
      <div>Email Edit</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Ref, ref } from "vue";
import EmailAccountList from "./EmailAccountList.vue";
import EmailAdd from "./EmailAdd.vue";
import { EmailStep } from "@/types";

const step: Ref<EmailStep> = ref("email-add");
</script>

<style scoped></style>
