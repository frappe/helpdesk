<template>
  <div class="flex h-screen w-screen justify-center bg-gray-100">
    <div class="mt-32 w-full px-4">
      <img
        v-if="configStore.brandLogo"
        :src="configStore.brandLogo"
        class="m-auto h-8"
      />
      <Logo v-else class="mx-auto h-8" />
      <div class="mt-6 flex items-center justify-center space-x-1.5">
        <span class="text-3xl font-semibold text-gray-900">Account Setup</span>
      </div>
      <div class="mx-auto mt-6 w-full px-4 sm:w-96">
        <form method="POST" @submit.prevent="submit">
          <FormControl
            v-model="email"
            variant="outline"
            size="md"
            type="email"
            label="Email"
            placeholder="john.doe@example.com"
            :disabled="authStore.verify.loading"
          />
          <FormControl
            v-model="password"
            class="mt-4"
            variant="outline"
            size="md"
            label="Password"
            placeholder="••••••"
            :disabled="authStore.verify.loading"
            type="password"
          />
          <ErrorMessage class="mt-2" :message="authStore.verify.error" />
          <Button
            variant="solid"
            class="mt-6 w-full"
            :loading="authStore.verify.loading"
          >
            Verify
          </Button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Button, FormControl } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import Logo from "~icons/logos/helpdesk";

const props = defineProps({
  requestKey: {
    type: String,
    required: true,
  },
});

const authStore = useAuthStore();
const configStore = useConfigStore();
const email = ref("");
const password = ref("");

function submit() {
  authStore.verify.submit({
    request_key: props.requestKey,
    email: email.value,
    password: password.value,
  }).promise;
}
</script>
