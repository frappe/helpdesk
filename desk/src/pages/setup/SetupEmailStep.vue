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

    <Transition
      mode="out-in"
      enter-active-class="transition duration-500 ease-out motion-reduce:transition-none"
      enter-from-class="opacity-0 translate-y-2"
      leave-active-class="transition duration-150 motion-reduce:transition-none"
      leave-to-class="opacity-0"
    >
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

        <div
          class="rounded-5 border border-outline-gray-1 p-4"
          aria-live="polite"
        >
          <div v-if="pull.error" class="flex items-start gap-3">
            <LucideCircleAlert
              class="mt-0.5 size-4 shrink-0 text-ink-red-5"
              aria-hidden="true"
            />
            <div class="min-w-0 space-y-0.5">
              <p class="text-base text-ink-gray-8">
                {{ __("Couldn't pull your tickets") }}
              </p>
              <ErrorMessage :message="pull.error" />
            </div>
          </div>
          <div v-else-if="!pull.fetched" class="flex items-start gap-3">
            <Spinner class="mt-0.5 size-4 text-ink-gray-5" />
            <div class="space-y-0.5">
              <p class="text-base text-ink-gray-8">
                {{ __("Pulling your tickets") }}
              </p>
              <p class="text-p-sm text-ink-gray-5">
                {{
                  __("Turning emails in {0} into tickets.", [
                    setup.mailbox.address,
                  ])
                }}
              </p>
            </div>
          </div>
          <div v-else class="flex items-start gap-3">
            <LucideCircleCheck
              class="mt-0.5 size-4 shrink-0 text-ink-green-5"
              aria-hidden="true"
            />
            <div class="min-w-0 space-y-0.5">
              <p class="text-base text-ink-gray-8">
                {{ __("Tickets successfully pulled") }}
              </p>
              <p class="truncate text-p-sm text-ink-gray-5">
                {{
                  setup.ticket
                    ? `#${setup.ticket.name} ${setup.ticket.subject}`
                    : __("New emails become tickets every few minutes.")
                }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </Transition>

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
  </section>
</template>

<script setup lang="ts">
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { useOnboarding } from "@framework/ui";
import { useEmailAccounts, useOneClick } from "@framework/ui/EmailAccounts";
import {
  Badge,
  Button,
  createListResource,
  createResource,
  dialog,
  ErrorMessage,
  Spinner,
  toast,
} from "frappe-ui";
import { onMounted, ref, watch } from "vue";
import SetupProviderPicker from "./SetupProviderPicker.vue";
import { type Mailbox, next, setup } from "./setup";

const { updateOnboardingStep } = useOnboarding("helpdesk") ?? {};
const controller = useEmailAccounts("HD Ticket");
const oneClick = useOneClick();
const picker = ref<InstanceType<typeof SetupProviderPicker> | null>(null);
const pickerScreen = ref("picker");

const firstTicket = createListResource({
  doctype: "HD Ticket",
  fields: ["name", "subject"],
  orderBy: "creation asc",
  pageLength: 1,
  onSuccess(tickets: { name: string; subject: string }[]) {
    if (tickets.length) setup.ticket = tickets[0];
  },
});
const pull = createResource({
  url: "frappe.email.doctype.email_account.email_account.pull_emails",
  onSuccess: () => firstTicket.reload(),
});
watch(
  () => setup.mailbox?.name,
  (mailbox) => {
    if (!mailbox) return;
    firstTicket.update({ filters: { email_account: mailbox } });
    pull.submit({ email_account: mailbox });
  },
  { immediate: true }
);

onMounted(() => {
  controller.load();
  const signIn = controller.signIn;
  if (!signIn || setup.mailbox) return;
  if (signIn.result !== "connected") {
    picker.value?.showSignInFailure(signIn.result, signIn.mailbox);
    return;
  }
  const stop = watch(
    () => signIn.account,
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
