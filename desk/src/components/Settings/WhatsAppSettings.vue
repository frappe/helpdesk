<template>
  <SettingsLayoutBase
    :description="
      __('Chat with customers over WhatsApp from the ticket conversation.')
    "
  >
    <template #title>
      <div class="flex items-center gap-2">
        <h1 class="text-lg font-semibold text-ink-gray-8">
          {{ __("WhatsApp") }}
        </h1>
        <Badge
          v-if="!isWhatsAppInstalled"
          theme="gray"
          variant="subtle"
          :label="__('Not installed')"
        />
        <Badge
          v-else-if="whatsAppEnabled"
          theme="green"
          variant="subtle"
          :label="__('Connected')"
        />
        <Badge
          v-else
          theme="orange"
          variant="subtle"
          :label="__('Not configured')"
        />
      </div>
    </template>

    <template #content>
      <!-- Transport app missing -->
      <div
        v-if="!isWhatsAppInstalled"
        class="flex items-start gap-3 rounded-md bg-surface-gray-1 p-4"
      >
        <WhatsAppIcon class="size-9 shrink-0 opacity-60" />
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">
            {{ __("Install the WhatsApp app") }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                "The frappe_whatsapp app provides the WhatsApp transport. Once it is installed and an account is active, a WhatsApp tab appears on every ticket."
              )
            }}
          </span>
        </div>
      </div>

      <div v-else class="flex flex-col gap-5">
        <!-- Accounts -->
        <div class="flex flex-col gap-2">
          <span class="text-sm font-medium text-ink-gray-7">
            {{ __("Accounts") }}
          </span>
          <div
            v-if="accounts.data?.length"
            class="divide-y rounded-md border border-outline-gray-2"
          >
            <div
              v-for="account in accounts.data"
              :key="account.name"
              class="flex items-center justify-between px-3 py-2"
            >
              <span class="text-p-sm text-ink-gray-8">
                {{ account.account_name || account.name }}
              </span>
              <Badge
                :theme="account.status === 'Active' ? 'green' : 'gray'"
                variant="subtle"
                :label="account.status"
              />
            </div>
          </div>
          <span v-else class="text-p-sm text-ink-gray-5">
            {{ __("No WhatsApp accounts configured yet.") }}
          </span>
        </div>

        <!-- Configuration lives in the transport app, not duplicated here -->
        <div class="flex flex-wrap gap-2">
          <Button
            :label="__('Manage accounts')"
            @click="openDeskPage('/app/whatsapp-account')"
          />
          <Button
            :label="__('Templates')"
            @click="openDeskPage('/app/whatsapp-templates')"
          />
          <Button
            :label="__('WhatsApp settings')"
            @click="openDeskPage('/app/whatsapp-settings')"
          />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { WhatsAppIcon } from "@/components/icons";
import { isWhatsAppInstalled, whatsAppEnabled } from "@/composables/whatsapp";
import { Badge, Button, createListResource } from "frappe-ui";

// The frappe_whatsapp DocTypes are only present when the transport app is
// installed; the list simply comes back empty otherwise. `auto: true` (not the
// non-reactive `isWhatsAppInstalled.value` snapshot, which is still false at
// setup while the install probe is in flight) so accounts load on first visit.
const accounts = createListResource({
  doctype: "WhatsApp Account",
  cache: "whatsapp-accounts",
  fields: ["name", "account_name", "status"],
  pageLength: 20,
  auto: true,
});

function openDeskPage(path: string) {
  window.open(path, "_blank");
}
</script>
