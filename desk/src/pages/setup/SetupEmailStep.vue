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
            <LucideMail class="size-4" aria-hidden="true" />
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
      <div
        v-if="setup.mailbox || pickerScreen === 'picker'"
        class="flex items-center justify-end gap-2"
      >
        <Button
          variant="outline"
          size="md"
          :label="__('Set up later')"
          @click="setUpLater"
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

<script lang="ts">
import { __ } from "@/translation";
import { useIntervalFn } from "@vueuse/core";
import { computed, ref, watch } from "vue";
import { setup } from "./setup";

const PHASE_SECONDS = 5;
const PHASES = [
  __("Knocking on your inbox…"),
  __("Turning emails into tickets…"),
  __("Starting the SLA clocks…"),
];
const waited = ref(0);
const clock = useIntervalFn(() => waited.value++, 1000, { immediate: false });
const phase = computed(() => Math.floor(waited.value / PHASE_SECONDS));
const ready = computed(() => phase.value >= PHASES.length);
watch(ready, (done) => {
  if (!done) return;
  clock.pause();
  setup.ticketArrived = true;
});
let startedFor: string | null = null;
</script>

<script setup lang="ts">
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { useOnboarding } from "@framework/ui";
import { useEmailAccounts, useOneClick } from "@framework/ui/EmailAccounts";
import {
  Badge,
  Button,
  createListResource,
  dialog,
  Spinner,
  toast,
} from "frappe-ui";
import { computed, onMounted, ref, watch } from "vue";
import Banner from "@framework/ui/components/EmailAccounts/Banner.vue";
import SetupProviderPicker from "./SetupProviderPicker.vue";
import { type Mailbox, next, setup } from "./setup";

const { updateOnboardingStep } = useOnboarding("helpdesk") ?? {};
const controller = useEmailAccounts("HD Ticket");
const oneClick = useOneClick();
const reveal = {
  enterActiveClass:
    "transition duration-300 ease-out motion-reduce:transition-none",
  enterFromClass: "opacity-0 translate-y-1",
  leaveActiveClass: "hidden",
};
watch(
  () => setup.mailbox?.name,
  (mailbox) => {
    if (!mailbox || startedFor === mailbox) return;
    startedFor = mailbox;
    waited.value = 0;
    clock.resume();
  },
  { immediate: true }
);
const picker = ref<InstanceType<typeof SetupProviderPicker> | null>(null);
const receiveOnly = ref(false);
const defaultOutgoing = computed(
  () => controller.accounts.find((a) => a.default_outgoing)?.email_id
);
const pickerScreen = ref("picker");

onMounted(() => {
  controller.load();
  const signIn = controller.signIn;
  if (!signIn || setup.mailbox) return;
  if (!["connected", "connected_receive_only"].includes(signIn.result)) {
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

function setUpLater() {
  dialog.confirm({
    title: __("Set up email later?"),
    message: __(
      "Without a connected mailbox, no tickets will be created from email. You can connect one from Settings."
    ),
    confirmLabel: __("Set up later"),
    cancelLabel: __("Stay here"),
    onConfirm: () => next({ skipped: true }),
  });
}
</script>
