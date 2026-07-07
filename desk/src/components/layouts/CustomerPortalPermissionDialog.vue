<template>
  <Dialog
    v-model:open="show"
    :title="__('Customer portal permissions have changed')"
  >
    <template #default>
      <div class="flex flex-col gap-3 text-p-base text-ink-gray-7">
        <p>
          {{
            __(
              "Contacts are now members of a customer, and only customer managers can see all tickets of their customer. Other contacts only see the tickets they have raised themselves."
            )
          }}
        </p>
        <p>
          {{
            __(
              "Contacts that existed before this update became regular members, so they may no longer see the other tickets of their customer."
            )
          }}
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
          :label="
            __(
              'Restore the previous behaviour by making every existing contact a customer manager'
            )
          "
        />
        <p class="text-p-sm text-ink-gray-5">
          {{ __("This notice will not be shown again after you confirm.") }}
        </p>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Confirm')"
        :loading="confirming"
        @click="confirm"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { createResource, toast } from "frappe-ui";
import { computed, ref, watch } from "vue";

const show = defineModel<boolean>();
const restoreOldBehaviour = ref(false);

const dismissResource = createResource({
  url: "helpdesk.api.customer_portal_notice.dismiss_notice",
  onSuccess: () => {
    show.value = false;
  },
});

const restoreResource = createResource({
  url: "helpdesk.api.customer_portal_notice.restore_ticket_access",
  onSuccess: () => {
    show.value = false;
    toast.success(
      __("Existing contacts are being made customer managers in the background")
    );
  },
});

const confirming = computed(
  () => dismissResource.loading || restoreResource.loading
);

function confirm() {
  if (restoreOldBehaviour.value) {
    restoreResource.submit();
  } else {
    dismissResource.submit();
  }
}

watch(
  () => show.value,
  (open) => {
    if (!open) restoreOldBehaviour.value = false;
  }
);
</script>
