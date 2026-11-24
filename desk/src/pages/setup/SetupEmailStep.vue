<template>
  <section class="space-y-8">
    <div class="space-y-1.5">
      <h1 class="text-2xl-semibold text-ink-gray-9">
        {{ __("Connect your support email") }}
      </h1>
      <p class="text-p-base text-ink-gray-6">
        {{ __("Emails sent to this mailbox become tickets in Helpdesk.") }}
      </p>
    </div>

    <Transition v-bind="reveal">
      <div v-if="!setup.mailbox" key="providers">
        <SetupProviderPicker
          ref="picker"
          :controller="controller"
          :one-click="oneClick.data || {}"
          @connected="onConnected"
          @screen="(s) => (pickerScreen = s)"
        />
      </div>

      <div v-else key="connected" class="space-y-4">
        <div
          class="flex items-center gap-3 rounded-5 border border-outline-gray-1 bg-surface-elevation-1 p-3"
        >
          <div
            class="flex size-9 shrink-0 items-center justify-center rounded-4 bg-surface-gray-2 text-ink-gray-7"
          >
            <img
              v-if="mailboxLogo"
              :src="mailboxLogo"
              alt=""
              class="size-5 object-contain"
            />
            <LucideMail v-else class="size-4" aria-hidden="true" />
          </div>
          <div class="min-w-0 flex-1">
            <p
              class="truncate text-base text-ink-gray-8"
              :title="setup.mailbox.address"
            >
              {{ setup.mailbox.address }}
            </p>
            <p class="text-sm text-ink-gray-5">{{ __("Incoming mail") }}</p>
          </div>
          <Badge :label="__('Connected')" theme="green" variant="subtle" />
        </div>

        <Banner
          v-if="receiveOnly"
          theme="amber"
          :title="__('Connected for receiving only')"
          :description="
            defaultOutgoing
              ? __(
                  'Microsoft doesn\'t let personal Outlook.com mailboxes send email from other apps. Replies go out from {0}.',
                  [defaultOutgoing]
                )
              : __(
                  'Microsoft doesn\'t let personal Outlook.com mailboxes send email from other apps. Replies go out from your default outgoing account.'
                )
          "
        />

        <div
          class="rounded-5 border border-outline-gray-1 p-4"
          aria-live="polite"
        >
          <div class="flex items-start gap-3">
            <span class="mt-0.5 flex size-4 shrink-0">
              <LucideCircleCheck
                v-if="ready"
                class="size-4 text-ink-green-5"
                aria-hidden="true"
              />
              <Spinner v-else class="size-4 text-ink-gray-5" />
            </span>
            <div class="min-w-0 flex-1">
              <Transition
                mode="out-in"
                enter-active-class="transition duration-300 ease-out motion-reduce:transition-none"
                enter-from-class="opacity-0 translate-y-1"
                leave-active-class="transition duration-200 ease-in motion-reduce:transition-none"
                leave-to-class="opacity-0 -translate-y-1"
              >
                <p
                  :key="ready ? 'ready' : phase"
                  class="text-base text-ink-gray-8"
                >
                  {{ ready ? __("Emails queued for import") : PHASES[phase] }}
                </p>
              </Transition>
              <div
                class="grid transition-[grid-template-rows,opacity] duration-300 ease-out motion-reduce:transition-none"
                :class="
                  ready
                    ? 'grid-rows-[1fr] opacity-100'
                    : 'grid-rows-[0fr] opacity-0'
                "
              >
                <div class="min-h-0 overflow-hidden">
                  <p class="truncate pt-0.5 text-p-sm text-ink-gray-5">
                    {{
                      __(
                        "Tickets will arrive shortly. You can proceed with the setup."
                      )
                    }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <Transition v-bind="reveal">
      <Alert
        v-if="confirmSkip"
        ref="skipQuestion"
        key="confirm-skip"
        :title="__('Skip email for now?')"
        :description="
          __(
            'Without a connected mailbox, no tickets will be created from email. You can connect one from Settings.'
          )
        "
        :icon="false"
        :primary-action="{
          label: __('Connect email'),
          variant: 'solid',
          onClick: () => (confirmSkip = false),
        }"
        :secondary-action="{
          label: __('Skip anyway'),
          onClick: () => next({ skipped: true }),
        }"
      />
      <div
        v-else-if="setup.mailbox || pickerScreen === 'picker'"
        key="actions"
        class="flex items-center justify-end gap-2"
      >
        <Button
          variant="outline"
          size="md"
          :label="__('Set up later')"
          @click="confirmSkip = true"
        />
        <Button
          variant="solid"
          theme="gray"
          size="md"
          :label="__('Continue')"
          :disabled="!setup.mailbox"
          @click="next()"
        />
      </div>
    </Transition>
  </section>
</template>

<script setup lang="ts">
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { useOnboarding } from "@framework/ui";
import { useEmailAccounts, useOneClick } from "@framework/ui/EmailAccounts";
import { Alert, Badge, Button, Spinner, toast } from "frappe-ui";
import { computed, nextTick, onMounted, ref, watch } from "vue";
import Banner from "@framework/ui/components/EmailAccounts/Banner.vue";
import { serviceOf } from "@framework/ui/components/EmailAccounts/services";
import SetupProviderPicker from "./SetupProviderPicker.vue";
import { IMPORT_PHASES, type Mailbox, useSetupFlow } from "./setup";

const PHASES = [
  __("Knocking on your inbox…"),
  __("Turning emails into tickets…"),
  __("Starting the SLA clocks…"),
];

const { importPhase: phase, next, reportError, setup } = useSetupFlow();
const ready = computed(() => phase.value >= IMPORT_PHASES);
const { updateOnboardingStep } = useOnboarding("helpdesk") ?? {};
const controller = useEmailAccounts("HD Ticket");
const mailboxLogo = computed(() => {
  const account = controller.accounts.find(
    (a) =>
      a.name === setup.mailbox?.name || a.email_id === setup.mailbox?.address
  );
  return account && serviceOf(account).logo;
});
const oneClick = useOneClick();
const reveal = {
  enterActiveClass:
    "transition duration-300 ease-out motion-reduce:transition-none",
  enterFromClass: "opacity-0 translate-y-1",
  leaveActiveClass: "hidden",
};
const picker = ref<InstanceType<typeof SetupProviderPicker> | null>(null);
const receiveOnly = ref(false);
const defaultOutgoing = computed(
  () => controller.accounts.find((a) => a.default_outgoing)?.email_id
);
const pickerScreen = ref("picker");
const confirmSkip = ref(false);
// Opening a provider leaves the list, so the question under it no longer applies.
watch(pickerScreen, () => (confirmSkip.value = false));
// On a short screen the question opens below the fold; the step scrolls to show it.
const skipQuestion = ref<{ $el: HTMLElement } | null>(null);
watch(confirmSkip, async (open) => {
  if (!open) return;
  await nextTick();
  skipQuestion.value?.$el?.scrollIntoView({
    block: "nearest",
    behavior: "smooth",
  });
});

onMounted(() => {
  controller.load();
  const signIn = controller.signIn;
  if (!signIn || setup.mailbox) return;
  if (!["connected", "connected_receive_only"].includes(signIn.result)) {
    reportError("email_sign_in", signIn.result);
    picker.value?.showSignInFailure(
      signIn.result,
      signIn.mailbox,
      signIn.provider
    );
    return;
  }
  receiveOnly.value = signIn.result === "connected_receive_only";
  const stop = watch(
    () =>
      signIn.account ??
      controller.accounts.find((a) => a.email_id === signIn.mailbox),
    (account) => {
      if (!account) return;
      stop();
      onConnected({ name: account.name, address: account.email_id });
    },
    { immediate: true }
  );
});

function onConnected(mailbox: Mailbox) {
  setup.mailbox = mailbox;
  toast.success(__("{0} connected", [mailbox.address]));
  updateOnboardingStep?.("setup_email_account");
  capture("email_account_created", { data: { source: "setup" } });
}
</script>
