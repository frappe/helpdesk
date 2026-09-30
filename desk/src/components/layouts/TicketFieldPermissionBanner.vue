<template>
  <template v-if="notice.data">
    <div
      v-if="!isSidebarCollapsed"
      class="flex flex-col gap-3 shadow-sm rounded-6 py-2.5 px-3 bg-surface-elevation-2 text-base"
    >
      <div class="inline-flex gap-2 text-ink-gray-9">
        <LucideShieldAlert class="h-4 w-4 my-0.5 shrink-0" />
        <div class="flex flex-col gap-0.5 text-p-sm">
          <div class="font-medium">
            {{ __("Ticket field permissions") }}
          </div>
          <div class="text-ink-gray-7">
            {{ __("Some ticket fields are now visible to agents only") }}
          </div>
        </div>
      </div>
      <Button
        :label="__('Learn more')"
        theme="blue"
        @click="showDialog = true"
      />
    </div>
    <Button v-else variant="ghost" @click="showDialog = true">
      <LucideShieldAlert class="h-4 w-4 shrink-0" />
    </Button>
    <Dialog
      v-model:open="showDialog"
      :title="__('Ticket field permissions have changed')"
    >
      <template #default>
        <div class="flex flex-col gap-3 text-p-base text-ink-gray-7">
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
          <p class="text-p-sm text-ink-gray-5">
            {{ __("You won't see this notice again.") }}
          </p>
        </div>
      </template>
      <template #actions>
        <Button
          class="w-full"
          variant="solid"
          :label="__('Got it')"
          :loading="dismissResource.loading"
          @click="dismissResource.submit()"
        />
      </template>
    </Dialog>
  </template>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { createResource } from "frappe-ui";
import { ref } from "vue";
import LucideShieldAlert from "~icons/lucide/shield-alert";

defineProps({
  isSidebarCollapsed: {
    type: Boolean,
    default: false,
  },
});

const showDialog = ref(false);

const notice = createResource({
  url: "frappe.client.get_single_value",
  params: {
    doctype: "HD Settings",
    field: "show_ticket_field_permission_notice",
  },
  auto: true,
});

const dismissResource = createResource({
  url: "helpdesk.api.customer_portal_notice.dismiss_field_permission_notice",
  onSuccess: () => {
    showDialog.value = false;
    notice.reload();
  },
});
</script>
