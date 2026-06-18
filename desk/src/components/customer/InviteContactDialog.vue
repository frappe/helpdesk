<template>
  <Dialog v-model:open="show" :title="__('Invite Contact')">
    <template #default>
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <div
            class="p-1 group bg-surface-gray-2 hover:bg-surface-gray-3 rounded w-full"
          >
            <EmailMultiSelect
              ref="emailMultiSelect"
              inputClass="!bg-surface-gray-2 hover:!bg-surface-gray-3 group-hover:!bg-surface-gray-3"
              :placeholder="__('Enter email address')"
              :existingUsers="excludedEmails"
              :additionalFilters="contactFilters"
              :forAgents="false"
              allowCustomEmail
              :validate="validateEmailWithZod"
              v-model="selectedContacts"
              :emptyPlaceholder="__('Type an email address')"
            />
          </div>
          <div class="flex items-center gap-1.5 text-p-xs text-ink-gray-5">
            <span>
              {{ __("Existing users join instantly. Others get an invite.") }}
            </span>
          </div>
        </div>
        <FormControl
          type="select"
          class="w-full [&>button]:w-full"
          v-model="role"
          :label="__('Role')"
          :options="roleOptions"
          :description="roleDescription"
        />
        <div v-if="pendingInvites.length" class="flex flex-col gap-3">
          <p class="text-base font-medium text-ink-gray-5">
            {{ __("Pending Invites") }}
          </p>
          <div class="flex flex-col gap-3 max-h-60 overflow-y-auto">
            <div
              v-for="invite in pendingInvites"
              :key="invite.name"
              class="flex items-center justify-between gap-2 min-w-0"
            >
              <div class="flex items-center gap-2 min-w-0">
                <div
                  class="flex size-8 shrink-0 items-center justify-center rounded-full border border-dashed border-outline-gray-3"
                >
                  <LucideUser class="size-4 text-ink-gray-5" />
                </div>
                <div class="flex flex-col gap-0.5 min-w-0">
                  <p class="text-base font-medium text-ink-gray-8 truncate">
                    {{ invite.email }}
                  </p>
                  <p class="text-sm text-ink-gray-5 truncate">
                    {{ __("Invited by") }} {{ invite.invited_by }} ·
                    {{ dayjsLocal(invite.invited_on).fromNow() }}
                  </p>
                </div>
              </div>
              <div class="flex justify-end min-w-[7rem] shrink-0">
                <RevokeInviteButton
                  :invite-name="invite.name"
                  @revoked="customer.getPendingInvites.reload()"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="solid"
          :label="__('Invite')"
          :loading="customer.addContacts.loading"
          :disabled="!selectedContacts.length"
          @click="inviteContacts"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import RevokeInviteButton from "@/components/customer/RevokeInviteButton.vue";
import EmailMultiSelect from "@/components/EmailMultiSelect.vue";
import { __ } from "@/translation";
import { CustomerResourceSymbol } from "@/types";
import {
  getErrorMessage,
  handleInviteUserSuccess,
  validateEmailWithZod,
} from "@/utils";
import { Button, Dialog, FormControl, dayjsLocal, toast } from "frappe-ui";
import { computed, inject, ref, watch } from "vue";
import LucideUser from "~icons/lucide/user";

const props = defineProps<{
  excludedEmails: string[];
}>();

const show = defineModel<boolean>({ default: false });

const customer = inject(CustomerResourceSymbol)!;

const emailMultiSelect = ref<{ setFocus: () => void } | null>(null);
const selectedContacts = ref<string[]>([]);
const role = ref("HD Customer");

interface PendingInvite {
  name: string;
  email: string;
  roles: string[];
  invited_by: string;
  invited_on: string;
}

interface InviteResult {
  invited_emails: string[];
  pending_invite_emails: string[];
  accepted_invite_emails: string[];
  disabled_user_emails: string[];
}

const roleOptions = [
  { value: "HD Customer", label: __("Customer") },
  { value: "HD Customer Manager", label: __("Customer Manager") },
];

const roleDescriptions: Record<string, string> = {
  "HD Customer": __(
    "Can raise tickets on behalf of the org and manage the tickets they raised."
  ),
  "HD Customer Manager": __(
    "Can view all tickets raised by the org and assign other members as managers."
  ),
};

const roleDescription = computed(() => roleDescriptions[role.value] ?? "");

const pendingInvites = computed<PendingInvite[]>(
  () => customer.getPendingInvites.data || []
);

const contactFilters = computed(() => {
  const filters: (string | string[])[][] = [["Contact", "user", "is", "set"]];
  if (props.excludedEmails.length) {
    filters.push(["Contact", "email_id", "not in", props.excludedEmails]);
  }
  return filters;
});

function inviteContacts() {
  customer.addContacts.submit(
    {
      contacts: JSON.stringify(selectedContacts.value),
      role: role.value,
    },
    {
      onSuccess() {
        const data: { added: string[]; invite_result: InviteResult } =
          customer.addContacts.data;
        selectedContacts.value = [];
        if (data.added.length) {
          toast.success(__("Contacts added successfully"));
          customer.getContacts.reload();
        }
        if (data.invite_result.invited_emails.length) {
          customer.getPendingInvites.reload();
        }
        handleInviteUserSuccess(data.invite_result);
      },
      onError(error: any) {
        getErrorMessage(error, true);
      },
    }
  );
}

watch(show, (val) => {
  if (!val) {
    selectedContacts.value = [];
    return;
  }
  customer.getPendingInvites.reload();
  setTimeout(() => emailMultiSelect.value?.setFocus(), 100);
});
</script>
