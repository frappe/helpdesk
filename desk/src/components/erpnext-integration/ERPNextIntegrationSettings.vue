<template>
  <template v-if="isAdmin || isManager">
    <hr class="my-8" />
    <div>
      <div class="text-base font-semibold text-ink-gray-9">
        {{ __("ERPNext Integration") }}
      </div>
      <div class="flex items-center justify-between mt-6">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">{{
            __("Enable ERPNext Integration")
          }}</span>
          <span class="text-p-sm text-ink-gray-6">{{
            __("Sync customers between Helpdesk and ERPNext automatically.")
          }}</span>
        </div>
        <Switch v-model="erpnextIntegrationEnabled" />
      </div>
    </div>
  </template>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
import { Error } from "@/types";
import { Switch, createResource, toast } from "frappe-ui";
import { ref, watch } from "vue";

const { isAdmin, isManager } = useAuthStore();

const erpnextIntegrationEnabled = ref(false);

const erpnextSettingsResource = createResource({
  url: "frappe.client.get",
  params: {
    doctype: "ERPNext HD Settings",
    name: "ERPNext HD Settings",
    fields: ["enabled"],
  },
  auto: true,
  onSuccess(data: any) {
    erpnextIntegrationEnabled.value = Boolean(data.enabled);
  },
});

const saveErpnextSettingsResource = createResource({
  url: "frappe.client.set_value",
  makeParams() {
    return {
      doctype: "ERPNext HD Settings",
      name: "ERPNext HD Settings",
      fieldname: {
        enabled: erpnextIntegrationEnabled.value,
      },
    };
  },
  onSuccess() {
    erpnextSettingsResource.reload();
  },
  onError(error: Error) {
    erpnextIntegrationEnabled.value = false;
    const msg = error.exc_type
      ? (error.messages || error.message || []).join(", ")
      : error.message;
    toast.error(msg);
  },
});

watch(erpnextIntegrationEnabled, async (newVal) => {
  if (!erpnextSettingsResource.data) return;
  if (newVal === Boolean(erpnextSettingsResource.data.enabled)) return;
  saveErpnextSettingsResource.submit().then(() => {
    if (newVal) {
      toast.success(__("ERPNext Integration is enabled"));
    } else {
      toast.success(__("ERPNext Integration is disabled"));
    }
  });
});
</script>
