<template>
  <section class="space-y-6">
    <div class="space-y-1">
      <h1 class="text-3xl text-ink-gray-9">{{ __("Invite your agents") }}</h1>
      <p class="text-p-base text-ink-gray-6">
        {{ __("They get an email with a link to join your Helpdesk.") }}
      </p>
    </div>

    <Alert
      v-if="inviteError"
      theme="red"
      :title="__('Some invites could not be sent')"
      :description="
        inviteError + ' ' + __('Invites already sent will not be sent again.')
      "
    />

    <div class="space-y-3">
      <div
        v-for="(row, i) in rows"
        :key="row.id"
        class="flex flex-wrap items-start gap-2 sm:flex-nowrap"
      >
        <div class="min-w-0 flex-1 basis-full sm:basis-auto">
          <FormControl
            v-model="row.email"
            type="text"
            :label="i === 0 ? __('Email') : undefined"
            :aria-label="__('Email {0}', [i + 1])"
            placeholder="name@company.com"
            :disabled="row.sent"
            :error="attempted || duplicates.has(row.id) ? errors[row.id] : undefined"
            :title="row.email"
            @keydown.enter.prevent="onEnter(i)"
          />
        </div>
        <div class="w-40 shrink-0">
          <FormControl
            v-model="row.role"
            type="select"
            :label="i === 0 ? __('Role') : undefined"
            :aria-label="__('Role {0}', [i + 1])"
            :options="roleOptions"
            :disabled="row.sent"
          />
        </div>
        <div
          class="flex h-7 w-16 shrink-0 items-center justify-end"
          :class="i === 0 ? 'sm:mt-[22px]' : ''"
        >
          <Badge v-if="row.sent" :label="__('Sent')" theme="gray" variant="subtle" />
          <Button
            v-else
            variant="ghost"
            :aria-label="__('Remove row')"
            @click="removeRow(row.id)"
          >
            <template #icon><LucideX class="size-4" /></template>
          </Button>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <Button
          variant="outline"
          :label="__('Add another')"
          :disabled="rows.length >= MAX_INVITE_ROWS"
          @click="addRow"
        >
          <template #prefix><LucidePlus class="size-4" /></template>
        </Button>
        <span v-if="rows.length >= MAX_INVITE_ROWS" class="text-sm text-ink-gray-5">
          {{ __("You can invite up to {0} at a time", [MAX_INVITE_ROWS]) }}
        </span>
      </div>
    </div>

    <div class="flex items-center justify-end gap-2 pt-2">
      <Button
        variant="outline"
        :label="__('Skip for now')"
        :disabled="sending || finishing"
        @click="emit('skip')"
      />
      <Button
        variant="solid"
        theme="gray"
        :label="sendLabel"
        :loading="sending || finishing"
        :disabled="!canSend"
        @click="send"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import {
  getInviteByEmailRoles,
  getInviteRoleOptions,
  type Role,
} from "@/components/Settings/inviteRoles";
import { useAuthStore } from "@/stores/auth";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { getErrorMessage, handleInviteUserSuccess } from "@/utils";
import { Alert, Badge, Button, FormControl, call, toast } from "frappe-ui";
import { computed, ref } from "vue";
import LucidePlus from "~icons/lucide/plus";
import LucideX from "~icons/lucide/x";
import {
  MAX_INVITE_ROWS,
  createInviteRow,
  groupUnsentByRole,
  normalizeEmail,
  validateRows,
  type InviteRow,
} from "./invites";

const rows = defineModel<InviteRow[]>("rows", { required: true });
defineProps<{ finishing: boolean }>();
const emit = defineEmits<{ done: []; skip: [] }>();

const authStore = useAuthStore();
const roleOptions = getInviteRoleOptions(authStore);

const attempted = ref(false);
const sending = ref(false);
const inviteError = ref("");

const validation = computed(() => validateRows(rows.value));
const errors = computed(() => validation.value.errors);
const duplicates = computed(() => validation.value.duplicates);

const unsentCount = computed(
  () => rows.value.filter((row) => !row.sent && normalizeEmail(row.email)).length
);
const canSend = computed(() => unsentCount.value > 0);
const sendLabel = computed(() =>
  unsentCount.value > 1
    ? __("Send {0} invites", [unsentCount.value])
    : __("Send invite")
);

function addRow() {
  if (rows.value.length < MAX_INVITE_ROWS) rows.value.push(createInviteRow());
}
function removeRow(id: number) {
  rows.value = rows.value.filter((row) => row.id !== id);
  if (!rows.value.length) rows.value = [createInviteRow()];
}
function onEnter(i: number) {
  const row = rows.value[i];
  const isLast = i === rows.value.length - 1;
  if (row && isLast && !errors.value[row.id] && normalizeEmail(row.email))
    addRow();
}

function markSent(role: Role, emails: string[]) {
  rows.value.forEach((row) => {
    if (row.role === role && emails.includes(normalizeEmail(row.email)))
      row.sent = true;
  });
}

async function send() {
  attempted.value = true;
  if (Object.keys(errors.value).length) return;
  const groups = Object.entries(groupUnsentByRole(rows.value)) as [Role, string[]][];
  if (!groups.length) return;

  sending.value = true;
  inviteError.value = "";
  try {
    for (const [role, emails] of groups) {
      const data = await call("frappe.core.api.user_invitation.invite_by_email", {
        emails: emails.join(","),
        roles: getInviteByEmailRoles(role),
        redirect_to_path: "/helpdesk",
        app_name: "helpdesk",
      });
      markSent(role, emails);
      handleInviteUserSuccess(data);
    }
  } catch (error) {
    inviteError.value = getErrorMessage(error);
    toast.error(inviteError.value);
    sending.value = false;
    return;
  }

  capture("agents_invited", {
    data: { count: rows.value.filter((row) => row.sent).length },
  });
  try {
    await call("helpdesk.api.onboarding.mark_checklist_steps", {
      steps: ["invite_agents"],
    });
  } catch {
    // best effort: the sidebar checklist can still be ticked by hand
  }
  sending.value = false;
  emit("done");
}
</script>
