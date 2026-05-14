<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Customers</div>
      </template>
      <template #right-header>
        <Button
          v-if="showSyncButton"
          :label="isSyncing ? 'Syncing…' : 'Sync with ERPNext'"
          theme="gray"
          variant="subtle"
          :loading="isSyncing"
          :disabled="isSyncing"
          @click="triggerErpnextSync"
        >
          <template v-if="!isSyncing" #prefix>
            <LucideRefreshCw class="h-4 w-4" />
          </template>
        </Button>
        <Button
          label="Create"
          theme="gray"
          variant="solid"
          @click="handleCreate"
        >
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </LayoutHeader>
    <ListViewBuilder
      ref="listViewRef"
      :options="options"
      @row-click="openCustomer"
      @empty-state-action="handleCreate"
    />
    <NewCustomerDialog
      v-model="isDialogVisible"
      @customer-created="handleCustomer"
    />
    <span v-if="isCustomerDialogVisible">
      <CustomerDialog
        v-model="isCustomerDialogVisible"
        :name="selectedCustomer"
        @customer-updated="handleCustomer(true)"
      />
    </span>
  </div>
</template>
<script setup lang="ts">
import NewCustomerDialog from "@/components/desk/global/NewCustomerDialog.vue";
import { OrganizationsIcon } from "@/components/icons";
import LayoutHeader from "@/components/LayoutHeader.vue";
import ListViewBuilder from "@/components/ListViewBuilder.vue";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";
import { Avatar, createResource, toast, usePageMeta } from "frappe-ui";
import { computed, h, onMounted, onUnmounted, ref } from "vue";
import CustomerDialog from "./CustomerDialog.vue";

const configStore = useConfigStore();
const { $socket } = globalStore();

const isDialogVisible = ref(false);
const isCustomerDialogVisible = ref(false);
const selectedCustomer = ref(null);
const listViewRef = ref(null);
const isSyncing = ref(false);
const { isManager, isAdmin } = useAuthStore();

const hasActiveFilters = computed(
  () => Object.keys(listViewRef.value?.list?.params?.filters || {}).length > 0
);

const isUnsynced = createResource({
  url: "helpdesk.helpdesk.integrations.erpnext.customer.is_unsynced",
  cache: ["ERPNext Sync Status", "HD Customer"],
  auto: true,
});

const showSyncButton = computed(() => {
  debugger;
  if (isUnsynced.loading) return false;
  if (
    configStore.isErpnextInstalled &&
    isUnsynced.data &&
    (isManager || isAdmin)
  ) {
    return true;
  }
});

function handleCreate() {
  isDialogVisible.value = true;
}

const syncResource = createResource({
  url: "helpdesk.helpdesk.integrations.erpnext.customer.sync_all_customers_with_erpnext",
  onSuccess() {
    toast.success(__("Sync complete"));
    listViewRef.value?.reload();
    isUnsynced.reload();
  },
  onError(err) {
    toast.error(err.messages?.[0] || __("Sync failed"));
  },
});

function triggerErpnextSync() {
  syncResource.submit();
}

function onSyncStart() {
  isSyncing.value = true;
}
function onSyncEnd() {
  isSyncing.value = false;
}

onMounted(() => {
  $socket.on("helpdesk:erpnext-sync-start", onSyncStart);
  $socket.on("helpdesk:erpnext-sync-end", onSyncEnd);
});
onUnmounted(() => {
  $socket.off("helpdesk:erpnext-sync-start", onSyncStart);
  $socket.off("helpdesk:erpnext-sync-end", onSyncEnd);
});

function openCustomer(id: string) {
  selectedCustomer.value = id;
  isCustomerDialogVisible.value = true;
}
function handleCustomer(updated = false) {
  updated
    ? (isCustomerDialogVisible.value = false)
    : (isDialogVisible.value = false);
  listViewRef.value?.reload();
}

const options = computed(() => {
  return {
    doctype: "HD Customer",
    selectable: true,
    showSelectBanner: true,
    columnConfig: {
      name: {
        prefix: ({ row }) => {
          return h(Avatar, {
            shape: "circle",
            image: row.image,
            label: row.name,
            size: "sm",
          });
        },
      },
    },

    emptyState: {
      title: "No customers found",
      description: hasActiveFilters.value
        ? __(
            "No customers found for the applied filters. Try adjusting or clearing your filters."
          )
        : undefined,
      icon: h(OrganizationsIcon, {
        class: "h-10 w-10",
      }),
    },
  };
});

usePageMeta(() => {
  return {
    title: "Customers",
  };
});
</script>
