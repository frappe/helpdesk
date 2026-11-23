<template>
  <TextInput
    v-model="url"
    :error="isBlurred ? linkError(url) : ''"
    @blur="isBlurred = true"
  />
</template>

<script setup lang="ts">
import { TextInput } from "frappe-ui";
import { ref } from "vue";
import { linkError } from "../utils";

const url = defineModel<string>({ default: "" });
const isBlurred = ref(false);
</script>
