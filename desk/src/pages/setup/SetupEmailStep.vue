<template>
  <section class="space-y-6">
    <div class="space-y-1">
      <h1 class="text-2xl-semibold text-ink-gray-9">
        {{ __("Connect your support email") }}
      </h1>
      <p class="text-p-base text-ink-gray-6">
        {{ __("Emails sent to this mailbox become tickets in Helpdesk.") }}
      </p>
    </div>

    <EmailAccounts doctype="HD Ticket" @created="onCreated" />

    <div
      v-if="connected"
      class="rounded-5 border border-outline-gray-1 p-4"
      aria-live="polite"
    >
      <div v-if="!arrived" class="flex items-start gap-3">
        <LucideLoader
          class="mt-0.5 size-4 shrink-0 text-ink-gray-5"
          :class="{ 'animate-spin': !timedOut }"
        />
        <div class="min-w-0 flex-1 space-y-0.5">
          <p class="text-base-medium text-ink-gray-8">
            {{ __("Waiting for your first ticket") }}
          </p>
          <p class="text-p-sm text-ink-gray-5">
            {{
              __("Send a test email to {0}. You can continue without waiting.", [
                status.data.email_address,
              ])
            }}
          </p>
        </div>
        <Button
          v-if="timedOut"
          variant="outline"
          size="sm"
          :label="__('Check again')"
          @click="checkAgain"
        />
      </div>
      <div v-else class="flex items-start gap-3">
        <LucideCircleCheck class="mt-0.5 size-4 shrink-0 text-ink-gray-8" />
        <p class="text-base-medium text-ink-gray-8">
          {{ __("Your first ticket has arrived") }}
        </p>
      </div>
    </div>

    <div class="flex items-center justify-end gap-2 pt-2">
      <Button
        v-if="!connected"
        variant="outline"
        :label="__('Set up later')"
        @click="confirmSetUpLater"
      />
      <Button
        variant="solid"
        theme="gray"
        :label="__('Continue')"
        @click="emit('next')"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { createDialog } from "@/components/dialogs";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { useDocumentVisibility } from "@vueuse/core";
import { EmailAccounts } from "@framework/ui/EmailAccounts";
import { Button, call } from "frappe-ui";
import { computed, onBeforeUnmount, ref, watch } from "vue";
import LucideCircleCheck from "~icons/lucide/circle-check";
import LucideLoader from "~icons/lucide/loader";
import { pollDelay } from "./polling";

const props = defineProps<{ status: any }>();
const emit = defineEmits<{ next: [] }>();

const connected = computed(() => !!props.status.data?.email_connected);
const arrived = computed(() => !!props.status.data?.ticket_arrived);

// Polling covers the return from provider sign-in, where @created never fires.
// It backs off and stops after a while; "Check again" starts it over.
const visibility = useDocumentVisibility();
const visible = computed(() => visibility.value !== "hidden");
const attempt = ref(0);
const timedOut = computed(() => pollDelay(attempt.value) === null);
let timer: ReturnType<typeof setTimeout> | undefined;

function schedule() {
  clearTimeout(timer);
  const delay = pollDelay(attempt.value);
  if (arrived.value || !visible.value || delay === null) return;
  timer = setTimeout(async () => {
    attempt.value++;
    try {
      await props.status.reload();
    } finally {
      schedule();
    }
  }, delay);
}

function checkAgain() {
  attempt.value = 0;
  props.status.reload();
  schedule();
}

watch([arrived, visible], schedule, { immediate: true });
onBeforeUnmount(() => clearTimeout(timer));

let ticked = false;
watch(
  connected,
  (isConnected) => {
    if (!isConnected || ticked) return;
    ticked = true;
    call("helpdesk.api.onboarding.mark_checklist_steps", {
      steps: ["setup_email_account"],
    }).catch(() => {
      // best effort: the sidebar checklist can still be ticked by hand
    });
  },
  { immediate: true }
);

function onCreated(service: string) {
  capture("email_account_created", { data: { service: service || "Custom" } });
  checkAgain();
}

function confirmSetUpLater() {
  createDialog({
    title: __("Set up email later?"),
    message: __(
      "Without a connected mailbox, no tickets will be created from email. You can connect one from Settings."
    ),
    actions: [
      { label: __("Stay here") },
      {
        label: __("Set up later"),
        variant: "solid",
        onClick: ({ close }: { close: () => void }) => {
          close();
          emit("next");
        },
      },
    ],
  });
}
</script>
