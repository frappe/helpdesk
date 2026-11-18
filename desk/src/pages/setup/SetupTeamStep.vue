<template>
  <section class="space-y-8">
    <div class="space-y-1.5">
      <h1 class="text-2xl-semibold text-ink-gray-9">
        {{ __("Invite your agents") }}
      </h1>
      <p class="text-p-base text-ink-gray-6">
        {{ __("They get an email with a link to join your Helpdesk.") }}
      </p>
    </div>

    <Alert
      v-if="failed.length"
      theme="red"
      :title="
        failed.length === 1
          ? __('1 invite could not be sent')
          : __('{0} invites could not be sent', [failed.length])
      "
      :description="
        __('Could not invite {0}: user is disabled.', [failed.join(', ')]) +
        ' ' +
        __('Already sent invites will not be sent again.')
      "
    />

    <div class="space-y-3">
      <div
        class="-mb-1.5 flex gap-2 text-xs text-ink-gray-5"
        aria-hidden="true"
      >
        <span class="flex-1">{{ __("Email") }}</span>
        <span class="w-40 shrink-0">{{ __("Role") }}</span>
        <span class="w-16 shrink-0" />
      </div>
      <TransitionGroup
        tag="div"
        class="relative flex flex-col gap-3"
        move-class="transition-transform duration-200 ease-out motion-reduce:transition-none"
        enter-active-class="transition duration-300 ease-out motion-reduce:transition-none"
        enter-from-class="opacity-0 -translate-y-1"
        leave-active-class="absolute inset-x-0 transition duration-150 motion-reduce:transition-none"
        leave-to-class="opacity-0"
      >
        <div
          v-for="(row, i) in setup.rows"
          :key="row.id"
          :data-invite-row="row.id"
          class="flex flex-wrap items-start gap-2 sm:flex-nowrap"
        >
          <div class="min-w-0 flex-1 basis-full sm:basis-auto">
            <FormControl
              v-model="row.email"
              type="text"
              :aria-label="__('Email {0}', [i + 1])"
              placeholder="name@company.com"
              :disabled="row.sent || sending"
              :error="rowErrors[row.id]"
              :title="row.email"
              @keydown.enter="onEnter(i)"
            />
          </div>
          <div class="w-40 shrink-0">
            <FormControl
              v-model="row.role"
              type="select"
              :aria-label="__('Role {0}', [i + 1])"
              :options="ROLE_OPTIONS"
              :disabled="row.sent || sending"
            />
          </div>
          <div class="flex h-7 w-16 shrink-0 items-center justify-end">
            <Badge
              v-if="row.sent"
              :label="__('Sent')"
              theme="green"
              variant="subtle"
            />
            <Tooltip v-else :text="__('Remove')">
              <Button
                variant="ghost"
                icon="lucide-x"
                :aria-label="__('Remove row')"
                :disabled="sending"
                @click="removeRow(row.id)"
              />
            </Tooltip>
          </div>
        </div>
      </TransitionGroup>

      <div class="flex items-center gap-3">
        <Button
          variant="outline"
          icon-left="lucide-plus"
          :label="__('Add another')"
          :disabled="sending || setup.rows.length >= MAX_ROWS || !lastRowFilled"
          @click="addRow"
        />
        <span
          v-if="setup.rows.length >= MAX_ROWS"
          class="text-sm text-ink-gray-5"
        >
          {{ __("You can invite up to {0} at a time", [MAX_ROWS]) }}
        </span>
      </div>
    </div>

    <div class="flex items-center justify-end gap-2">
      <Button
        variant="outline"
        size="md"
        :label="__('Skip and finish')"
        :disabled="sending"
        @click="next({ skipped: !invited.length })"
      />
      <Button
        variant="solid"
        theme="gray"
        size="md"
        :label="
          !unsentCount
            ? __('Continue')
            : unsentCount > 1
            ? __('Send {0} invites', [unsentCount])
            : __('Send invite')
        "
        :loading="sending"
        :disabled="!hasValidEmail"
        @click="sendInvites"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import {
  AGENT_ROLES,
  type AgentRole,
  getInviteByEmailRoles,
  handleInviteUserSuccess,
  validateEmailWithZod,
} from "@/utils";
import { useOnboarding } from "@framework/ui";
import {
  Alert,
  Badge,
  Button,
  call,
  FormControl,
  toast,
  Tooltip,
} from "frappe-ui";
import { useTimeoutFn } from "@vueuse/core";
import { computed, nextTick, ref } from "vue";
import { normalizeEmail, type InviteRow, useSetupFlow } from "./setup";

const { invited, newRow, next, setup } = useSetupFlow();

type InviteResult = Parameters<typeof handleInviteUserSuccess>[0];

const MAX_ROWS = 20;
const NEXT_STEP_DELAY_MS = 1800;
const ROLE_OPTIONS = AGENT_ROLES.map((role) => ({
  label: __(role),
  value: role,
}));

const { updateOnboardingStep } = useOnboarding("helpdesk") ?? {};
const attempted = ref(false);
const blocked = ref<number | null>(null);
const sending = ref(false);
const failed = ref<string[]>([]);
const moveOn = useTimeoutFn(
  () => {
    sending.value = false;
    next();
  },
  NEXT_STEP_DELAY_MS,
  { immediate: false }
);

const rowErrors = computed(() => {
  const seen = new Set<string>();
  const errors: Record<number, string> = {};
  for (const row of setup.rows) {
    const email = normalizeEmail(row.email);
    if (!email && row.id === blocked.value)
      errors[row.id] = __("Enter an email first");
    if (!email || row.sent) {
      if (email) seen.add(email);
      continue;
    }
    if (seen.has(email))
      errors[row.id] = __("This email is already in the list");
    else if (attempted.value && !validateEmailWithZod(email))
      errors[row.id] = __("Enter a valid email address");
    seen.add(email);
  }
  return errors;
});
const pendingRows = computed(() =>
  setup.rows.filter((r) => !r.sent && normalizeEmail(r.email))
);
const hasValidEmail = computed(() =>
  pendingRows.value.some(
    (r) =>
      validateEmailWithZod(normalizeEmail(r.email)) && !rowErrors.value[r.id]
  )
);
const unsentCount = computed(() => pendingRows.value.length);
const lastRowFilled = computed(() => {
  const last = setup.rows[setup.rows.length - 1];
  return last.sent || !!normalizeEmail(last.email);
});

function addRow() {
  const unfinished = setup.rows.find(
    (r) =>
      !r.sent &&
      (!validateEmailWithZod(normalizeEmail(r.email)) || rowErrors.value[r.id])
  );
  if (unfinished) {
    attempted.value = true;
    blocked.value = unfinished.id;
    nextTick(() =>
      document
        .querySelector<HTMLInputElement>(
          `[data-invite-row="${unfinished.id}"] input`
        )
        ?.focus()
    );
    return;
  }
  if (setup.rows.length < MAX_ROWS) setup.rows.push(newRow());
}

function removeRow(id: number) {
  setup.rows = setup.rows.filter((r) => r.id !== id);
  if (!setup.rows.length) setup.rows = [newRow()];
}

function onEnter(i: number) {
  const last = i === setup.rows.length - 1;
  if (last && validateEmailWithZod(normalizeEmail(setup.rows[i].email)))
    addRow();
}

async function sendInvites() {
  attempted.value = true;
  const rows = pendingRows.value;
  if (Object.keys(rowErrors.value).length) return;
  if (
    !rows.length ||
    rows.some((r) => !validateEmailWithZod(normalizeEmail(r.email)))
  )
    return;
  sending.value = true;
  const summary: InviteResult = {
    disabled_user_emails: [],
    accepted_invite_emails: [],
    pending_invite_emails: [],
    invited_emails: [],
  };
  try {
    for (const role of AGENT_ROLES) {
      const group = rows.filter((r) => r.role === role);
      if (!group.length) continue;
      const result = await invite(role, group);
      for (const key of Object.keys(summary) as (keyof InviteResult)[])
        summary[key].push(...result[key]);
    }
  } catch (e) {
    toast.error(e.messages?.join(" ") || __("Could not send invites"));
  }
  handleInviteUserSuccess(summary);
  failed.value = summary.disabled_user_emails;
  const members = new Set(summary.accepted_invite_emails);
  setup.rows = setup.rows.filter(
    (r) =>
      (r.sent || normalizeEmail(r.email)) &&
      !members.has(normalizeEmail(r.email))
  );
  if (!setup.rows.length) setup.rows = [newRow()];
  const sent = rows.filter((r) => r.sent).length;
  if (sent) updateOnboardingStep?.("invite_agents");
  if (failed.value.length || !sent) {
    sending.value = false;
    return;
  }
  moveOn.start();
}

async function invite(
  role: AgentRole,
  rows: InviteRow[]
): Promise<InviteResult> {
  const result = await call("frappe.core.api.user_invitation.invite_by_email", {
    emails: rows.map((r) => normalizeEmail(r.email)).join(","),
    roles: getInviteByEmailRoles(role),
    redirect_to_path: "/helpdesk",
    app_name: "helpdesk",
  });
  const sentTo = new Set([
    ...result.invited_emails,
    ...result.pending_invite_emails,
  ]);
  for (const row of rows) row.sent ||= sentTo.has(normalizeEmail(row.email));
  capture("agents_invited", { data: { role, source: "setup" } });
  return result;
}
</script>
