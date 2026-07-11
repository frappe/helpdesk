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
              "Earlier, every contact could see all the tickets of their company. Now, contacts only see the tickets they raised themselves."
            )
          }}
        </p>
        <p>
          {{
            __(
              "Only customer managers can see every ticket of their company and manage its contacts."
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
          :label="__('Make all existing contacts customer managers')"
        />
        <p class="text-p-sm text-ink-gray-5">
          {{ __("You won't see this notice again.") }}
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
    dismissResource.submit();
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
