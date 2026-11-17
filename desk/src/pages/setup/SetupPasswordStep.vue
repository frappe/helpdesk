<template>
  <form class="space-y-8" @submit.prevent="save">
    <div class="space-y-1.5">
      <h1 class="text-2xl-semibold text-ink-gray-9">
        {{ __("Welcome. Set your password") }}
      </h1>
      <p class="text-p-base text-ink-gray-6">
        {{ __("You signed up as") }}
        <span class="text-ink-gray-8">{{ authStore.userId }}</span
        >. {{ __("Use this password to log in to") }}
        <span class="text-ink-gray-8">{{ site }}</span
        >.
      </p>
    </div>

    <div class="space-y-4">
      <div>
        <div class="flex h-5 items-center justify-between gap-2">
          <label for="setup-new-password" class="text-xs text-ink-gray-5">
            {{ __("New password") }}
          </label>
          <span
            v-if="strength.label"
            class="text-sm text-ink-gray-5"
            aria-live="polite"
          >
            {{ __("Strength:") }}
            <span class="text-sm-medium" :class="strength.ink">{{
              strength.label
            }}</span>
          </span>
        </div>
        <Password
          id="setup-new-password"
          v-model="setup.password"
          class="mt-1.5"
          placeholder="••••••••"
          autocomplete="new-password"
          autofocus
        />
        <div
          class="grid transition-[grid-template-rows,opacity] duration-200 ease-out motion-reduce:transition-none"
          :class="
            showHint
              ? 'grid-rows-[1fr] opacity-100'
              : 'grid-rows-[0fr] opacity-0'
          "
        >
          <div class="min-h-0 overflow-hidden">
            <p class="pt-1.5 text-p-sm text-ink-gray-5">
              {{
                __(
                  "At least 8 characters. Mixing in numbers and symbols makes it stronger."
                )
              }}
            </p>
          </div>
        </div>
      </div>

      <div>
        <label for="setup-confirm-password" class="text-xs text-ink-gray-5">
          {{ __("Confirm new password") }}
        </label>
        <Password
          id="setup-confirm-password"
          v-model="confirmPassword"
          class="mt-1.5"
          placeholder="••••••••"
          autocomplete="new-password"
        />
        <div
          class="grid transition-[grid-template-rows,opacity] duration-200 ease-out motion-reduce:transition-none"
          :class="
            mismatch
              ? 'grid-rows-[1fr] opacity-100'
              : 'grid-rows-[0fr] opacity-0'
          "
        >
          <div class="min-h-0 overflow-hidden">
            <p class="pt-1.5 text-p-sm text-ink-red-6" role="alert">
              {{ __("The passwords you entered do not match.") }}
            </p>
          </div>
        </div>
      </div>

      <div
        class="grid transition-[grid-template-rows,opacity] duration-200 ease-out motion-reduce:transition-none"
        :class="
          saveError
            ? 'grid-rows-[1fr] opacity-100'
            : 'grid-rows-[0fr] opacity-0'
        "
      >
        <div class="min-h-0 overflow-hidden">
          <ErrorMessage :message="saveError" />
        </div>
      </div>
    </div>

    <Button
      type="submit"
      variant="solid"
      theme="gray"
      size="md"
      class="w-full"
      :label="__('Confirm')"
      :disabled="!canSave"
      :loading="saving"
    />
  </form>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
import { refDebounced, watchDebounced } from "@vueuse/core";
import {
  Button,
  call,
  createResource,
  ErrorMessage,
  Password,
} from "frappe-ui";
import { computed, ref } from "vue";
import { next, setup } from "./setup";

const MIN_LENGTH = 8;
const authStore = useAuthStore();
const site = window.location.host;

const score = createResource({
  url: "helpdesk.api.setup.get_password_score",
  makeParams: () => ({ password: setup.password }),
});
watchDebounced(
  () => setup.password,
  (password) => {
    if (password) score.submit();
    else score.reset();
  },
  { debounce: 250 }
);

const STRENGTH = computed(() => [
  { label: __("Too weak"), ink: "text-ink-red-6" },
  { label: __("Too weak"), ink: "text-ink-red-6" },
  { label: __("Okay"), ink: "text-ink-amber-6" },
  { label: __("Good"), ink: "text-ink-green-6" },
  { label: __("Strong"), ink: "text-ink-green-6" },
]);
const currentScore = computed<number | null>(() =>
  setup.password && score.data ? score.data.score : null
);
const strength = computed(
  () => STRENGTH.value[currentScore.value ?? -1] ?? { label: "", ink: "" }
);
const acceptable = computed(
  () =>
    setup.password.length >= MIN_LENGTH &&
    currentScore.value !== null &&
    currentScore.value >= score.data.minimum
);

const showHint = computed(
  () => !!setup.password && currentScore.value !== null && !acceptable.value
);

const confirmPassword = ref("");
const settledConfirm = refDebounced(confirmPassword, 500);
const matches = computed(() => confirmPassword.value === setup.password);
const mismatch = computed(() => !!settledConfirm.value && !matches.value);
const canSave = computed(
  () => acceptable.value && !!confirmPassword.value && matches.value
);

const saving = ref(false);
const saveError = ref("");

async function save() {
  if (!canSave.value || saving.value) return;
  saving.value = true;
  saveError.value = "";
  try {
    await call("frappe.client.set_value", {
      doctype: "User",
      name: authStore.userId,
      fieldname: { new_password: setup.password, logout_all_sessions: 0 },
    });
    next();
  } catch (e) {
    saveError.value =
      e.messages?.join(" ") || __("Could not save your password");
  } finally {
    saving.value = false;
  }
}
</script>
