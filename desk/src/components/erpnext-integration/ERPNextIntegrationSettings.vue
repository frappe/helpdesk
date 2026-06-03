<template>
  <SettingsLayoutBase
    :description="__('Sync customers between Helpdesk and ERPNext.')"
  >
    <template #title>
      <div class="flex items-center gap-2">
        <h1 class="text-lg font-semibold text-ink-gray-8">
          {{ __("ERPNext") }}
        </h1>
        <Badge
          v-if="installed === false"
          theme="gray"
          variant="subtle"
          :label="__('Not installed')"
        />
      </div>
    </template>
    <template #content>
      <div class="flex items-center justify-between gap-4">
        <div class="flex min-w-0 items-center gap-3">
          <ErpnextIcon
            class="size-9 shrink-0"
            :class="{ 'opacity-60': installed === false }"
          />
          <div class="flex min-w-0 flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __("Enable ERPNext Integration") }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __("Sync customers between Helpdesk and ERPNext.") }}
            </span>
          </div>
        </div>
        <div
          v-if="installed === false"
          class="cursor-not-allowed"
          @click="showNotInstalledToast"
        >
          <Switch :model-value="false" disabled class="pointer-events-none" />
        </div>
        <Switch v-else v-model="erpnextIntegrationEnabled" />
      </div>

      <div
        v-if="installed === false"
        class="mt-4 flex items-center gap-2 text-p-sm text-ink-gray-6"
      >
        <LucideInfo class="h-4 w-4 shrink-0 text-ink-gray-5" />
        <span>
          {{
            __("Install the ERPNext app on your site to use this integration.")
          }}
        </span>
      </div>

      <div
        v-else-if="erpnextIntegrationEnabled"
        class="mt-4 flex items-center gap-3 rounded-lg p-3"
        :class="inSync ? 'bg-surface-green-1' : 'bg-surface-amber-1'"
      >
        <div
          class="grid size-7 shrink-0 place-items-center"
          :class="inSync ? ' text-ink-green-3' : ' text-ink-amber-3'"
        >
          <LucideCheck v-if="inSync" class="h-4 w-4" />
          <LucideTriangleAlert v-else class="h-4 w-4" />
        </div>
        <div class="flex min-w-0 flex-1 flex-col">
          <span class="text-p-sm font-medium text-ink-gray-8">
            {{
              inSync
                ? __("Customers are in sync")
                : __("Sync your existing customers")
            }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              inSync
                ? __(
                    "New and updated customers sync automatically between Helpdesk and ERPNext."
                  )
                : __(
                    "Run an initial sync to reconcile existing records. New ones update automatically."
                  )
            }}
          </span>
        </div>
        <Button
          v-if="!inSync"
          theme="gray"
          variant="subtle"
          class="border border-outline-gray-2 bg-surface-white hover:bg-surface-white hover:border-outline-gray-3 active:bg-surface-gray-2 focus-visible:bg-surface-white focus-visible:ring-2 focus-visible:ring-outline-gray-3"
          :loading="isSyncing || syncAction.loading"
          :disabled="isSyncing || syncAction.loading"
          :label="isSyncing ? __('Syncing…') : __('Sync now')"
          @click="syncAction.submit()"
        >
          <template v-if="!isSyncing && !syncAction.loading" #prefix>
            <LucideRefreshCw class="h-4 w-4" />
          </template>
        </Button>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import { ErpnextIcon } from "@/components/icons";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";
import { Error } from "@/types";
import { Badge, Button, Switch, createResource, toast } from "frappe-ui";
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import LucideCheck from "~icons/lucide/check";
import LucideInfo from "~icons/lucide/info";
import LucideRefreshCw from "~icons/lucide/refresh-cw";
import LucideTriangleAlert from "~icons/lucide/triangle-alert";

const { $socket } = globalStore();

const erpnextIntegrationEnabled = ref(false);
const isSyncing = ref(false);

const syncInfoResource = createResource({
  url: "helpdesk.integrations.erpnext.api.get_sync_info",
  onSuccess(data: any) {
    erpnextIntegrationEnabled.value = Boolean(data?.enabled);
  },
});

const installed = window.apps?.includes("erpnext") ?? false;
const inSync = computed(() => Boolean(syncInfoResource.data?.in_sync));

const saveResource = createResource({
  url: "frappe.client.set_value",
  makeParams() {
    return {
      doctype: "ERPNext HD Settings",
      name: "ERPNext HD Settings",
      fieldname: { enabled: erpnextIntegrationEnabled.value },
    };
  },
  onSuccess() {
    syncInfoResource.reload();
    toast.success(
      erpnextIntegrationEnabled.value
        ? __("ERPNext Integration is enabled")
        : __("ERPNext Integration is disabled")
    );
  },
  onError(error: Error) {
    erpnextIntegrationEnabled.value = false;
    const msg = error.exc_type
      ? (error.messages || error.message || []).join(", ")
      : error.message;
    toast.error(msg);
  },
});

const syncAction = createResource({
  url: "helpdesk.integrations.erpnext.api.sync_hd_erpnext_customers",
  onSuccess() {
    toast.success(__("Sync started"));
  },
});

function showNotInstalledToast() {
  toast.error(
    __(
      "ERPNext is not installed on your site. Please install ERPNext to enable this setting."
    )
  );
}

function onSyncStart() {
  isSyncing.value = true;
}

function onSyncEnd() {
  isSyncing.value = false;
  syncInfoResource.reload();
  toast.success(__("Sync completed successfully"));
}

watch(erpnextIntegrationEnabled, (newVal) => {
  if (syncInfoResource.data?.enabled === undefined) return;
  if (newVal === Boolean(syncInfoResource.data.enabled)) return;
  saveResource.submit();
});

onMounted(() => {
  syncInfoResource.reload();
  $socket.on("helpdesk:erpnext-sync-start", onSyncStart);
  $socket.on("helpdesk:erpnext-sync-end", onSyncEnd);
});

onUnmounted(() => {
  $socket.off("helpdesk:erpnext-sync-start", onSyncStart);
  $socket.off("helpdesk:erpnext-sync-end", onSyncEnd);
});
</script>
