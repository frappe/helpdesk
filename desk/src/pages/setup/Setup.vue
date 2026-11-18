<template>
  <div class="grid min-h-screen bg-surface-base lg:grid-cols-2">
    <section class="flex min-h-screen flex-col px-4 py-5 sm:px-8">
      <header class="flex h-8 items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <HDLogo class="size-6 shrink-0 rounded-4" aria-hidden="true" />
          <span class="text-base font-medium text-ink-gray-9">{{
            __("Helpdesk")
          }}</span>
        </div>
        <div class="flex items-center gap-1">
          <Button
            v-if="!currentStep?.required"
            variant="ghost"
            class="text-ink-gray-6"
            :label="__('Skip setup')"
            @click="confirmSkip = true"
          />
          <Tooltip :text="themeMenu.label">
            <Dropdown :options="themeMenu.submenu">
              <Button
                variant="ghost"
                icon="lucide-sun-moon"
                :aria-label="themeMenu.label"
              />
            </Dropdown>
          </Tooltip>
        </div>
      </header>

      <main
        class="mx-auto flex w-full max-w-md flex-1 flex-col justify-center py-10"
      >
        <div class="flex h-7 items-center justify-between">
          <span class="text-sm text-ink-gray-6">{{ stepOf }}</span>
          <Button
            v-if="canGoBack"
            variant="ghost"
            size="sm"
            class="-me-2"
            icon-left="lucide-arrow-left"
            :label="__('Back')"
            @click="back"
          />
        </div>
        <Progress
          class="mt-2"
          :value="progress"
          :intervals="steps.length"
          size="sm"
          :aria-label="stepOf"
        />
        <div class="mt-8">
          <Transition
            mode="out-in"
            enter-active-class="transition duration-500 ease-out motion-reduce:transition-none"
            enter-from-class="opacity-0 translate-y-3"
            leave-active-class="transition duration-200 ease-in motion-reduce:transition-none"
            leave-to-class="opacity-0 -translate-y-1"
          >
            <component :is="STEP_VIEWS[setup.step]" :key="setup.step" />
          </Transition>
        </div>
      </main>

      <TelemetryConsent
        app-name="helpdesk"
        class="mx-auto w-full max-w-md"
        :label="__('Share anonymous usage data to help improve Helpdesk')"
        :error-message="__('Could not save your choice. Please try again.')"
      />
    </section>

    <aside class="sticky top-0 hidden h-screen min-w-0 lg:block">
      <SetupPreview />
    </aside>

    <Dialog
      v-model:open="confirmSkip"
      :title="__('Skip setup?')"
      :message="__('You can do all of this later from Settings.')"
      size="sm"
      :actions="[
        { label: __('Cancel'), onClick: ({ close }) => close() },
        { label: __('Skip setup'), variant: 'solid', onClick: skipAll },
      ]"
    />

    <SetupDoneDialog
      :open="setup.showDone"
      :connected="!!setup.mailbox"
      :agents="invited"
      :ask-feedback="telemetry.isEnabled"
      @close="goToHelpdesk"
    />
  </div>
</template>

<script setup lang="ts">
import HDLogo from "@/assets/logos/HDLogo.vue";
import { __ } from "@/translation";
import { TelemetryConsent, useTelemetry } from "@framework/ui";
import { useThemeMenuItem } from "@helpdesk/shared/themeMenu";
import { Button, Dialog, Dropdown, Progress, Tooltip } from "frappe-ui";
import { computed, ref } from "vue";
import SetupDoneDialog from "./SetupDoneDialog.vue";
import SetupEmailStep from "./SetupEmailStep.vue";
import SetupPasswordStep from "./SetupPasswordStep.vue";
import SetupPreview from "./SetupPreview.vue";
import SetupTeamStep from "./SetupTeamStep.vue";
import SetupWorkspaceStep from "./SetupWorkspaceStep.vue";
import {
  back,
  canGoBack,
  currentStep,
  invited,
  openDesk,
  setup,
  skipSetup,
  startSetup,
  stepIndex,
  steps,
} from "./setup";

const STEP_VIEWS = {
  password: SetupPasswordStep,
  workspace: SetupWorkspaceStep,
  email: SetupEmailStep,
  team: SetupTeamStep,
};

const telemetry = useTelemetry();
const themeMenu = useThemeMenuItem();
const confirmSkip = ref(false);

const stepOf = computed(() =>
  __("Step {0} of {1}", [stepIndex.value + 1, steps.value.length])
);
const progress = computed(
  () => ((stepIndex.value + 1) / steps.value.length) * 100
);

const backFromSignIn = new URLSearchParams(window.location.search).has(
  "email_oauth"
);
startSetup(backFromSignIn ? "email" : undefined);

function skipAll({ close }: { close: () => void }) {
  close();
  skipSetup();
}

function goToHelpdesk() {
  openDesk();
}
</script>
