<template>
  <div class="space-y-8">
    <div class="space-y-1.5">
      <h1 class="text-2xl-semibold text-ink-gray-9">
        {{ __("Set your password") }}
      </h1>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            "You are signed in, but have no password yet. Set one so you can sign in again from any device."
          )
        }}
      </p>
    </div>
    <PasswordStep
      :labels="labels"
      @input="(length) => (setup.passwordLength = length)"
      @ready="(ready) => (setup.passwordReady = ready)"
      @done="saved"
    />
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { PasswordStep } from "@framework/ui";
import { useSetupFlow } from "./setup";

const { next, setup } = useSetupFlow();

const labels = {
  label: __("Password"),
  placeholder: "••••••••",
  hint: __(
    "At least 8 characters. Mixing in numbers and symbols makes it stronger."
  ),
  show: __("Show password"),
  hide: __("Hide password"),
  save: __("Save"),
  failed: __("Could not save your password"),
  confirmLabel: __("Confirm password"),
  confirmPlaceholder: "••••••••",
  mismatch: __("The passwords you entered do not match."),
  strength: __("Strength:"),
  levels: [__("Poor"), __("Poor"), __("Average"), __("Good"), __("Great")] as [
    string,
    string,
    string,
    string,
    string
  ],
};

function saved() {
  window.needs_password_setup = false;
  setup.passwordLength = 0;
  next();
}
</script>
