<template>
  <div class="h-full flex flex-col gap-10 text-ink-gray-8">
    <!-- Header -->
    <div class="flex justify-between gap-x-2">
      <div class="flex flex-col gap-1 w-9/12">
        <component
          :is="`h${props.titleHeadingLvl}`"
          class="text-lg font-semibold"
        >
          Send invites to
        </component>
        <p class="text-p-base text-ink-gray-6">
          {{ props.description }}
        </p>
      </div>
      <div class="flex item-center justify-end">
        <Button
          label="Send invites"
          variant="solid"
          :disabled="invitees.length === 0 || emailInputErrorMsgs.length > 0"
          @click="() => props.inviteByEmailResource.submit()"
          :loading="props.inviteByEmailResource.loading"
        />
      </div>
    </div>
    <!-- Main content -->
    <div class="flex flex-col gap-10 overflow-y-auto">
      <div>
        <div>
          <label
            :for="inviteByEmailInputId"
            class="block text-xs text-ink-gray-5 mb-1.5"
          >
            Invite by email
          </label>
          <MultiSelect
            :inputId="inviteByEmailInputId"
            variant="subtle"
            noOptionsFoundMsg="Type an email address to invite"
            inputClass="!bg-surface-gray-2 hover:!bg-surface-gray-3 group-hover:!bg-surface-gray-3"
            :values="props.invitees"
            @update:values="(values) => emits('update:invitees', values)"
            :isValidValue="validateEmail"
            :getValidationErrorMsg="
              (email) => `${email} is an invalid email address`
            "
            class="p-2 group bg-surface-gray-2 hover:bg-surface-gray-3 rounded"
            :options="[]"
            placeholder="john@doe.com"
          >
            <template #option="{ option }">
              <UserAvatar class="mr-2" :name="option.value" size="lg" />
              <div class="flex flex-col gap-1 p-1 text-ink-gray-8">
                <div class="text-base font-medium">
                  {{ option.label }}
                </div>
                <div class="text-sm text-ink-gray-5">
                  {{ option.value }}
                </div>
              </div>
            </template>
          </MultiSelect>
          <div
            aria-live="polite"
            class="text-xs text-ink-red-3 mt-1.5 flex flex-col gap-y-1"
            :class="emailInputErrorMsgs.length > 0 ? '' : 'sr-only'"
          >
            <div v-for="msg in emailInputErrorMsgs" :key="msg">{{ msg }}</div>
          </div>
        </div>
        <FormControl
          type="select"
          class="mt-6"
          :value="props.selectedRole"
          @change="(e: any) => emits('update:selectedRole', e.target.value)"
          label="Invite as"
          :options="
            props.roleOptions.map((role) => ({
              value: role.value,
              label: props.roleToLabel[role.value],
            }))
          "
          :description="roleToDescription[props.selectedRole]"
        />
      </div>
      <template
        v-if="
          props.pendingInvitesResource.data?.length && invitees.length === 0
        "
      >
        <section class="flex flex-col gap-4">
          <component
            :is="`h${props.titleHeadingLvl + 1}`"
            class="flex text-base font-semibold"
          >
            Pending Invites
          </component>
          <ul class="flex flex-col gap-1">
            <li
              class="flex items-center justify-between px-3 py-1 rounded-lg bg-surface-gray-2"
              v-for="pendingInvite in props.pendingInvitesResource.data"
              :key="pendingInvite.name"
            >
              <div class="text-base">
                <span class="text-ink-gray-8">
                  {{ pendingInvite.email }}
                </span>
                <span class="text-ink-gray-5">
                  ({{ props.roleToLabel[pendingInvite.role as TRole] }})
                </span>
              </div>
              <div>
                <Tooltip text="Delete Invitation">
                  <div>
                    <Button
                      icon="x"
                      variant="ghost"
                      :loading="
                        props.pendingInvitesResource.delete.loading &&
                        props.pendingInvitesResource.delete.params.name ===
                          pendingInvite.name
                      "
                      @click="
                        props.pendingInvitesResource.delete.submit(
                          pendingInvite.name
                        )
                      "
                    />
                  </div>
                </Tooltip>
              </div>
            </li>
          </ul>
        </section>
      </template>
    </div>
    <ErrorMessage :message="props.errorMsg" />
  </div>
</template>

<script setup lang="ts" generic="TRole extends string">
import { computed } from "vue";
import { Button, FormControl, Tooltip } from "frappe-ui";
import MultiSelect from "./MultiSelectInput.vue";
import { validateEmail } from "@/utils";
import { getEmailsErrorMsg, getId } from "./helpers";

type RoleProp = { value: TRole; description: string };

const inviteByEmailInputId = getId();

const props = defineProps<{
  titleHeadingLvl: 1 | 2 | 3 | 4 | 5;
  description: string;
  inviteByEmailResource: any;
  existingEmails: readonly string[];
  roleOptions: readonly [RoleProp, ...RoleProp[]];
  roleToLabel: Record<TRole, string>;
  selectedRole: TRole;
  invitees: string[];
  pendingInvitesResource: any;
  errorMsg?: string | null;
}>();

const emits = defineEmits<{
  "update:selectedRole": [TRole];
  "update:invitees": [string[]];
}>();

const getInviteesInList = (lst: readonly string[]) => {
  if (props.invitees.length === 0 || lst.length === 0) {
    return [];
  }
  const inviteesSet = new Set(props.invitees);
  const inviteesInList: string[] = [];
  for (const lstItem of lst) {
    if (inviteesSet.has(lstItem)) {
      inviteesInList.push(lstItem);
    }
  }
  return inviteesInList;
};
const existingEmailInviteesMsg = computed(() => {
  const existingEmailInvitees = getInviteesInList(props.existingEmails);
  return existingEmailInvitees.length > 0
    ? getEmailsErrorMsg(existingEmailInvitees, "present")
    : null;
});
const pendingInviteesMsg = computed(() => {
  const pendingInviteesEmail = getInviteesInList(
    (props.pendingInvitesResource.data ?? []).map(
      (invitee: { email: string }) => invitee.email
    )
  );
  return pendingInviteesEmail.length > 0
    ? getEmailsErrorMsg(pendingInviteesEmail, "invited")
    : null;
});
const emailInputErrorMsgs = computed(() => {
  const errorMsgs: string[] = [];
  if (existingEmailInviteesMsg.value) {
    errorMsgs.push(existingEmailInviteesMsg.value);
  }
  if (pendingInviteesMsg.value) {
    errorMsgs.push(pendingInviteesMsg.value);
  }
  return errorMsgs;
});
const roleToDescription = computed(() => {
  const res: Record<string, string> = {};
  for (const { value, description } of props.roleOptions) {
    res[value] = description;
  }
  return res;
});
</script>
