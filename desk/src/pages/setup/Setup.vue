<template>
  <div class="relative flex min-h-screen flex-col overflow-y-auto bg-surface-white">
    <header
      class="absolute inset-x-0 top-0 z-20 flex flex-wrap items-center justify-between gap-x-3 gap-y-2 px-3 py-3 sm:px-5"
    >
      <div class="flex items-center gap-2">
        <HDLogo class="size-7" />
        <span class="text-lg-semibold text-ink-gray-9">{{ __("Helpdesk") }}</span>
      </div>
      <div class="flex items-center gap-1">
        <Button v-if="step === 2" variant="ghost" :label="__('Back')" @click="step = 1">
          <template #prefix><LucideArrowLeft class="size-4" /></template>
        </Button>
        <Button
          variant="ghost"
          :label="__('Skip setup')"
          :disabled="finishing"
          @click="confirmSkip"
        />
      </div>
    </header>

    <div class="flex min-h-0 flex-1">
      <main class="flex w-full flex-col lg:w-[560px] lg:shrink-0">
        <div class="flex-1 px-3 pb-10 pt-20 sm:px-8 lg:px-12 lg:pt-[12vh]">
          <div class="mx-auto w-full max-w-[480px]">
            <div class="mb-8 space-y-2">
              <p class="text-sm-medium text-ink-gray-6">
                {{ __("Step {0} of {1}", [step, TOTAL_STEPS]) }}
              </p>
              <Progress
                :value="(step / TOTAL_STEPS) * 100"
                :intervals="TOTAL_STEPS"
                size="sm"
                role="progressbar"
                :aria-valuenow="step"
                aria-valuemin="1"
                :aria-valuemax="TOTAL_STEPS"
                :aria-label="__('Step {0} of {1}', [step, TOTAL_STEPS])"
              />
            </div>

            <Transition
              mode="out-in"
              enter-active-class="transition duration-500 ease-out motion-reduce:transition-none"
              enter-from-class="opacity-0 translate-y-3"
              leave-active-class="transition duration-200 ease-in motion-reduce:transition-none"
              leave-to-class="opacity-0 -translate-y-1"
            >
              <SetupEmailStep
                v-if="step === 1"
                key="email"
                :status="status"
                @next="step = 2"
              />
              <SetupInviteStep
                v-else
                key="invite"
                v-model:rows="rows"
                :finishing="finishing"
                @done="finish(false)"
                @skip="finish(true)"
              />
            </Transition>
          </div>
        </div>

        <footer class="border-t border-outline-gray-1 px-3 py-4 sm:px-8 lg:px-12">
          <div class="mx-auto w-full max-w-[480px]">
            <Checkbox
              :model-value="telemetry"
              :label="__('Share usage data')"
              :disabled="!status.data"
              @update:model-value="saveTelemetry"
            />
            <p class="mt-1 pl-6 text-p-xs text-ink-gray-5">
              {{ __("Helps us improve Helpdesk. Saved as soon as you change it.") }}
            </p>
          </div>
        </footer>
      </main>

      <SetupPreview />
    </div>
  </div>

  <SetupFeedbackDialog :open="showFeedback" @close="closeFeedback" />
</template>

<script setup lang="ts">
import HDLogo from "@/assets/logos/HDLogo.vue";
import { createDialog } from "@/components/dialogs";
import { useAuthStore } from "@/stores/auth";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { getErrorMessage } from "@/utils";
import { useTelemetry } from "@framework/ui";
import { Button, Checkbox, Progress, call, createResource, toast } from "frappe-ui";
import { ref, watch } from "vue";
import { useRouter } from "vue-router";
import LucideArrowLeft from "~icons/lucide/arrow-left";
import SetupEmailStep from "./SetupEmailStep.vue";
import SetupFeedbackDialog from "./SetupFeedbackDialog.vue";
import SetupInviteStep from "./SetupInviteStep.vue";
import SetupPreview from "./SetupPreview.vue";
import { createInviteRow, type InviteRow } from "./invites";

const TOTAL_STEPS = 2;

const router = useRouter();
const authStore = useAuthStore();
const telemetryClient = useTelemetry();

const step = ref<1 | 2>(1);
const rows = ref<InviteRow[]>([createInviteRow()]);
const finishing = ref(false);
const showFeedback = ref(false);

const status = createResource({
  url: "helpdesk.api.onboarding.get_setup_status",
  method: "GET",
  auto: true,
  onError() {
    // One toast however often the poll fails; the flow itself stays usable.
    toast.error(__("Couldn't check your email setup"), {
      id: "setup-status-error",
      description: __("You can keep going. We'll try again shortly."),
    });
  },
});

// The saved value wins, so an earlier opt-out stays opted out. Read once: polling must
// not undo a toggle that is still saving.
const telemetry = ref(true);
let telemetrySeeded = false;
watch(
  () => status.data?.telemetry_enabled,
  (enabled) => {
    if (enabled === undefined || telemetrySeeded) return;
    telemetrySeeded = true;
    telemetry.value = !!enabled;
  },
  { immediate: true }
);

async function saveTelemetry(enabled: boolean) {
  const previous = telemetry.value;
  telemetry.value = enabled;
  try {
    await call("helpdesk.api.onboarding.set_telemetry_enabled", { enabled });
    if (!enabled) telemetryClient.disable();
  } catch (error) {
    telemetry.value = previous;
    toast.error(getErrorMessage(error, false, __("Could not save this setting")));
  }
}

async function finish(skipped: boolean) {
  finishing.value = true;
  try {
    await call("helpdesk.api.onboarding.complete_setup", { skipped });
  } catch (error) {
    finishing.value = false;
    toast.error(getErrorMessage(error, false, __("Could not finish setup")));
    return;
  }
  authStore.markSetupDone();
  finishing.value = false;
  // capture does nothing while telemetry is off, so there is nobody to ask
  if (telemetryClient.isEnabled) showFeedback.value = true;
  else goHome();
}

function confirmSkip() {
  createDialog({
    title: __("Skip setup?"),
    message: __("You can connect email and invite agents later from Settings."),
    actions: [
      { label: __("Keep going") },
      {
        label: __("Skip setup"),
        variant: "solid",
        onClick: async ({ close }: { close: () => void }) => {
          close();
          await finish(true);
        },
      },
    ],
  });
}

function closeFeedback(feedback: { rating: number; comment: string } | null) {
  if (feedback) {
    capture("setup_feedback", { data: feedback });
    toast.success(__("Thanks for the feedback"));
  }
  showFeedback.value = false;
  goHome();
}

function goHome() {
  router.replace({ name: "Home" });
}
</script>
