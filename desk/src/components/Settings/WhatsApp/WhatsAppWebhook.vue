<template>
  <section class="flex flex-col gap-3">
    <h2 class="text-base-medium text-ink-gray-8">
      {{ __("Webhook") }}
    </h2>
    <p class="text-p-sm text-ink-gray-6">
      {{
        __(
          "In your Meta app, open WhatsApp > Configuration, paste the Callback URL and the Verify token below, then subscribe to the messages and message_template_status_update fields."
        )
      }}
    </p>
    <div class="flex items-end gap-2">
      <TextInput
        class="min-w-0 flex-1"
        :label="__('Callback URL')"
        :model-value="webhookUrl"
        readonly
        data-testid="whatsapp-webhook-url"
      />
      <Button
        icon="lucide-copy"
        :tooltip="__('Copy')"
        :aria-label="__('Copy webhook URL')"
        @click="copyToClipboard(webhookUrl)"
      />
    </div>
    <template v-if="settings.doc">
      <Alert
        v-if="!settings.originalDoc?.webhook_secret"
        theme="amber"
        :title="
          __(
            'Without the App secret, anyone who knows the Callback URL can send fake messages.'
          )
        "
        data-testid="whatsapp-secret-warning"
      />
      <div class="grid gap-3 sm:grid-cols-2">
        <TextInput
          v-model="settings.doc.webhook_verify_token"
          :label="__('Verify token')"
          :placeholder="__('Any text you choose')"
        />
        <Password
          v-model="settings.doc.webhook_secret"
          :label="__('App secret')"
          :description="__('Meta app > App settings > Basic')"
        />
      </div>
    </template>
  </section>
  <ConfirmDialog
    v-model="confirming"
    :title="__('Unsaved changes')"
    :message="
      __(
        'Are you sure you want to leave the webhook settings? Unsaved changes will be lost.'
      )
    "
    :on-confirm="confirm"
  />
</template>

<script setup lang="ts">
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import { __ } from "@/translation";
import { copyToClipboard } from "@helpdesk/shared/utils";
import { Alert, Button, Password, TextInput, toast } from "frappe-ui";
import { computed } from "vue";
import { useUnsavedGuard } from "./useUnsavedGuard";

const props = defineProps<{ settings: any }>();

const webhookUrl = `${window.location.origin}/api/method/whatsapp.whatsapp.webhook.handler`;

const isDirty = computed(() => Boolean(props.settings.isDirty));
const saving = computed(() => Boolean(props.settings.save.loading));
const { confirming, leave, confirm } = useUnsavedGuard(() => isDirty.value);

function save() {
  props.settings.save.submit(undefined, {
    onSuccess: () => toast.success(__("Webhook settings saved")),
  });
}

/** Runs `action`, first asking to drop unsaved edits, which the shared copy would otherwise keep. */
function leaveDiscarding(action: () => void) {
  leave(() => {
    if (isDirty.value) props.settings.reload();
    action();
  });
}

defineExpose({ isDirty, saving, save, leave: leaveDiscarding });
</script>
