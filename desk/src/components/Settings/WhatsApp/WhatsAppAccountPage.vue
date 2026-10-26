<template>
  <SettingsLayoutBase
    :back-label="name || __('New account')"
    :on-back="() => leave(() => emit('back'))"
    :dirty="isDirty && !account.isNew"
  >
    <template v-if="loaded && (isDirty || account.isNew)" #header-actions>
      <Button
        :label="account.isNew ? __('Create') : __('Save')"
        :loading="account.saving"
        theme="gray"
        variant="solid"
        @click="save"
      />
    </template>
    <template #content>
      <div
        v-if="account.loading"
        class="flex items-center justify-center py-16 text-ink-gray-5"
      >
        <LoadingIndicator class="size-4" />
      </div>
      <Alert
        v-else-if="!loaded"
        theme="red"
        :title="__('Could not load this account')"
        :primary-action="{ label: __('Retry'), onClick: account.reload }"
        data-testid="whatsapp-account-error"
      />
      <AccountForm v-else :controller="account" />
    </template>
  </SettingsLayoutBase>
  <ConfirmDialog
    v-model="confirming"
    :title="__('Unsaved changes')"
    :message="
      __('Are you sure you want to go back? Unsaved changes will be lost.')
    "
    :on-confirm="confirm"
  />
</template>

<script setup lang="ts">
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { __ } from "@/translation";
import { AccountForm, useAccount } from "@whatsapp/ui";
import { Alert, Button, LoadingIndicator, toast } from "frappe-ui";
import { computed } from "vue";
import { useUnsavedGuard } from "./useUnsavedGuard";

const props = defineProps<{ name: string }>();
const emit = defineEmits<{ back: [] }>();

const account = useAccount({ name: () => props.name });
// An existing account counts as loaded once the server copy is in the form.
const loaded = computed(() => account.isNew || Boolean(account.doc.name));
const isDirty = computed(() => loaded.value && account.isDirty);
const { confirming, leave, confirm } = useUnsavedGuard(() => isDirty.value);

/** Create goes back to the list; the form shows a failed save itself. */
async function save() {
  const wasNew = account.isNew;
  if (!(await account.save())) return;
  toast.success(wasNew ? __("Account created") : __("Account updated"));
  if (wasNew) emit("back");
}
</script>
