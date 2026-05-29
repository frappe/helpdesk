<template>
  <Button
    v-if="showSyncButton"
    theme="gray"
    variant="subtle"
    :loading="isSyncing || syncAction.loading"
    :disabled="isSyncing || syncAction.loading"
    @click="syncAction.submit()"
  >
    <template v-if="!isSyncing && !syncAction.loading" #prefix>
      <LucideRefreshCw class="h-4 w-4" />
    </template>
    <span>
      {{ isSyncing ? __("Syncing…") : __("Sync Customers with ERPNext") }}
    </span>
  </Button>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";
import { Button, createResource, toast } from "frappe-ui";
import { computed, onMounted, onUnmounted, ref } from "vue";
import LucideRefreshCw from "~icons/lucide/refresh-cw";

const emit = defineEmits<{
  synced: [];
}>();

const { isManager, isAdmin } = useAuthStore();
const { $socket } = globalStore();
const isSyncing = ref(false);

const syncInfo = createResource({
  url: "helpdesk.integrations.erpnext.api.get_sync_info",
  cache: ["ERPNextCustomerSyncInfo"],
  auto: true,
});

const showSyncButton = computed(() => {
  if (!syncInfo.data?.enabled) return false;
  return !!(!syncInfo.data?.in_sync && (isManager || isAdmin));
});

const syncAction = createResource({
  url: "helpdesk.integrations.erpnext.api.sync_hd_erpnext_customers",
  onSuccess() {
    toast.success(__("Sync started"));
    emit("synced");
  },
});

function onSyncStart() {
  isSyncing.value = true;
}

function onSyncEnd() {
  isSyncing.value = false;
  syncInfo.reload();
  toast.success(__("Sync completed successfully"));
  emit("synced");
}

onMounted(() => {
  $socket.on("helpdesk:erpnext-sync-start", onSyncStart);
  $socket.on("helpdesk:erpnext-sync-end", onSyncEnd);
});

onUnmounted(() => {
  $socket.off("helpdesk:erpnext-sync-start", onSyncStart);
  $socket.off("helpdesk:erpnext-sync-end", onSyncEnd);
});
</script>
