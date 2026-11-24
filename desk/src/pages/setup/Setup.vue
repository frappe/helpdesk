<template>
  <SetupFlow
    v-model:step="setup.step"
    :steps="steps"
    :labels="labels"
    @finish="finishSetup"
  >
    <template #brand>
      <div class="flex items-center gap-2">
        <HDLogo class="size-6 shrink-0 rounded-4" aria-hidden="true" />
        <span class="text-base font-medium text-ink-gray-9">{{
          __("Frappe Helpdesk")
        }}</span>
      </div>
    </template>
    <template #step="{ step, done, skip, handleBack }">
      <Transition
        mode="out-in"
        enter-active-class="transition duration-500 ease-out motion-reduce:transition-none"
        enter-from-class="opacity-0 translate-y-3"
        leave-active-class="transition duration-200 ease-in motion-reduce:transition-none"
        leave-to-class="opacity-0 -translate-y-1"
        @before-leave="(el) => ((el as HTMLElement).inert = true)"
      >
        <component
          :is="STEP_VIEWS[step.name as StepKey]"
          :key="step.name"
          v-bind="bindStep({ done, skip, handleBack })"
        />
      </Transition>
    </template>
    <template #footer>
      <TelemetryConsent
        app-name="helpdesk"
        class="mx-auto w-full max-w-md"
        :label="
          __('Help improve Frappe Helpdesk by sharing anonymous usage data')
        "
        :error-message="__('Could not save your choice. Please try again.')"
      />
    </template>
    <template #preview>
      <SetupPreview />
    </template>
  </SetupFlow>

  <SetupDoneDialog
    :open="setup.showDone"
    :connected="!!setup.mailbox"
    :agents="invited"
    :ask-feedback="telemetry.isEnabled"
    @close="openDesk"
  />
</template>

<script setup lang="ts">
import HDLogo from "@/assets/logos/HDLogo.vue";
import { __ } from "@/translation";
import { SetupFlow, TelemetryConsent, useTelemetry } from "@framework/ui";
import { useEventListener } from "@vueuse/core";
import SetupDoneDialog from "./SetupDoneDialog.vue";
import SetupEmailStep from "./SetupEmailStep.vue";
import SetupPasswordStep from "./SetupPasswordStep.vue";
import SetupPreview from "./SetupPreview.vue";
import SetupTeamStep from "./SetupTeamStep.vue";
import SetupWorkspaceStep from "./SetupWorkspaceStep.vue";
import { provideSetupFlow, type StepKey } from "./setup";

const STEP_VIEWS = {
  password: SetupPasswordStep,
  workspace: SetupWorkspaceStep,
  email: SetupEmailStep,
  team: SetupTeamStep,
};

const { bindStep, finishSetup, holdEnter, invited, openDesk, setup, steps } =
  provideSetupFlow();

useEventListener(window, "keydown", holdEnter, { capture: true });

const telemetry = useTelemetry();

const labels = {
  back: __("Back"),
  skip: __("Skip setup"),
  skipTitle: __("Skip setup?"),
  skipMessage: __("You can do all of this later from Settings."),
  cancel: __("Cancel"),
  darkMode: __("Switch to dark mode"),
  lightMode: __("Switch to light mode"),
  stepOf: (step: number, total: number) => __("Step {0} of {1}", [step, total]),
};
</script>
