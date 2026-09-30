<template>
  <SidebarBanner
    banner="ticket_field_permission"
    :title="__('Ticket field permissions')"
    :description="__('Some ticket fields are now visible to agents only')"
    :dialog-title="__('Ticket field permissions have changed')"
    :is-sidebar-collapsed="isSidebarCollapsed"
  >
    <p>
      {{
        __(
          "Ticket fields now use permission levels. Customers can read fields at level 7, and only agents can read fields at level 8."
        )
      }}
    </p>
    <p>
      {{
        __(
          "After raising a ticket, customers can only close it, rate it and change the fields marked Editable after creation in the ticket template."
        )
      }}
    </p>
    <p>
      {{
        __(
          "Roles you created get level 7 only. Add level 8 in Role Permission Manager for your own agent roles."
        )
      }}
      {{ __("Learn more in the") }}
      <a
        href="https://docs.frappe.io/helpdesk/customization/perm-levels-in-helpdesk"
        target="_blank"
        class="underline"
        >{{ __("documentation") }}</a
      >.
    </p>
  </SidebarBanner>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import SidebarBanner from "./SidebarBanner.vue";

defineProps<{ isSidebarCollapsed: boolean }>();
</script>
