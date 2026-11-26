<template>
  <SidebarBanner
    banner="customer_portal_permission"
    :title="__('Customer portal update')"
    :description="__('We have changed how customer portal permissions work')"
    :dialog-title="__('Customer portal permissions have changed')"
    :confirm-label="__('Confirm')"
    :before-dismiss="restoreTicketAccess"
    :is-sidebar-collapsed="isSidebarCollapsed"
    @update:open="clearChoiceOnClose"
  >
    <p>
      {{
        __(
          "Earlier, every contact could see all the tickets of their company. Now, contacts only see the tickets they raised themselves."
        )
      }}
    </p>
    <p>
      {{ __("Only users with the role of ") }}
      <span class="font-semibold text-ink-gray-8"
        >'{{ __("Customer Manager") }}'
      </span>
      {{ __("can see every ticket of their company and manage its contacts.") }}
      {{ __("Learn more in the") }}
      <a
        href="https://docs.frappe.io/helpdesk/customers-contacts#update-on-permissions"
        target="_blank"
        class="underline"
        >{{ __("documentation") }}</a
      >.
    </p>
    <FormControl
      v-model="restoreOldBehaviour"
      type="checkbox"
      :label="__('Make all existing contacts customer managers')"
    />
  </SidebarBanner>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { createResource, toast } from "frappe-ui";
import { ref } from "vue";
import SidebarBanner from "./SidebarBanner.vue";

defineProps<{ isSidebarCollapsed: boolean }>();

const restoreOldBehaviour = ref(false);

const restoreResource = createResource({
  url: "helpdesk.api.customer_portal_notice.restore_ticket_access",
  onSuccess: () => {
    toast.success(
      __("Existing contacts are being made customer managers in the background")
    );
  },
});

function clearChoiceOnClose(open: boolean) {
  if (!open) restoreOldBehaviour.value = false;
}

async function restoreTicketAccess() {
  if (restoreOldBehaviour.value) await restoreResource.submit();
}
</script>
