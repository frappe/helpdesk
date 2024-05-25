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
        <span class="text-3xl font-semibold text-gray-900">Login</span>
      </div>
      <div class="mx-auto mt-6 w-full px-4 sm:w-96">
        <form
          v-if="showEmailLogin"
          method="POST"
          action="/api/method/login"
          @submit.prevent="submit"
        >
          <div>
            <FormControl
              v-model="email"
              variant="outline"
              size="md"
              :type="
                (email || '').toLowerCase() === 'administrator'
                  ? 'text'
                  : 'email'
              "
              label="Email"
              placeholder="john.doe@example.com"
              :disabled="authStore.login.loading"
            />
          </div>
          <div class="mt-4">
            <FormControl
              v-model="password"
              variant="outline"
              size="md"
              label="Password"
              placeholder="••••••"
              :disabled="authStore.login.loading"
              type="password"
            />
          </div>
          <ErrorMessage class="mt-2" :message="authStore.login.error" />
          <Button
            variant="solid"
            class="mt-6 w-full"
            :loading="authStore.login.loading"
          >
            Login
          </Button>
          <RouterLink :to="{ name: SIGNUP }">
            <button
              v-if="!authProviders.data.length"
              class="mt-2 w-full py-2 text-base text-gray-600"
              @click="showEmailLogin = false"
            >
              Don't have an account? Signup
            </button>
          </RouterLink>
          <button
            v-if="authProviders.data.length"
            class="mt-2 w-full py-2 text-base text-gray-600"
            @click="showEmailLogin = false"
          >
            Login using other methods
          </button>
        </form>
        <div
          v-if="authProviders.data && !showEmailLogin"
          class="mx-auto space-y-2"
        >
          <Button variant="solid" class="w-full" @click="showEmailLogin = true">
            Login via email
          </Button>
          <a
            v-for="provider in authProviders.data"
            :key="provider.name"
            class="block h-7 w-full rounded border bg-gray-900 px-3 py-1 text-center text-base text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-400"
            :href="provider.auth_url"
          >
            Login via {{ provider.provider_name }}
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { createResource, Button, FormControl } from "frappe-ui";
import { SIGNUP } from "@/router";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import Logo from "~icons/logos/helpdesk";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const configStore = useConfigStore();
const showEmailLogin = ref(false);
const email = ref("");
const password = ref("");
const authProviders = createResource({
  url: "helpdesk.api.auth.oauth_providers",
  auto: true,
  onSuccess(data) {
    showEmailLogin.value = data.length === 0;
  },
});

function submit() {
  authStore.login
    .submit({
      usr: email.value,
      pwd: password.value,
    })
    .then(() => {
      if (route.query.redirect) {
        router.replace({ path: route.query.redirect as string });
      }
    });
}
</script>
