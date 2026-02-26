<template>
  <div
    class="min-w-96 rounded-md bg-surface-white border border-gray-200 px-3 py-2.5 flex flex-col gap-2.5"
  >
    <div class="flex items-center justify-between">
      <div class="flex gap-2 items-center min-w-0">
        <Avatar
          size="lg"
          :shape="'circle'"
          :image="contact.image ?? ''"
          :label="contact.contact_name"
        />
        <p
          class="truncate min-w-0"
          :class="contact.is_manager || contact.is_primary ? 'max-w-[50%]' : ''"
        >
          {{ contact.contact_name }}
        </p>
        <Badge v-if="contact.is_primary" :label="__('Primary')" theme="blue" />
        <Tooltip
          v-if="contact.is_manager"
          :text="__('Manager')"
          placement="top"
        >
          <LucideBriefcase class="h-4 w-4 text-ink-gray-6" />
        </Tooltip>
      </div>
      <Dropdown
        placement="right"
        :options="dropdownOptions"
        v-if="hasPermission()"
      >
        <Button class="h-6 w-6 p-0" variant="ghost">
          <LucideMoreHorizontal class="h-4 w-4 text-ink-gray-6" />
        </Button>
      </Dropdown>
    </div>
    <div class="border-t border-gray-200 w-full" />
    <div class="flex flex-col gap-3">
      <template v-for="(item, index) in contactDetails" :key="item.value">
        <div
          class="flex items-center gap-2 text-sm text-ink-gray-8 font-[420]"
          :class="item.class?.(item.value)"
        >
          <component
            :is="item.icon"
            class="h-4 w-4 text-ink-gray-6"
            :class="item.color?.(item.value)"
          />
          <span
            class="text-ink-gray-8"
            :class="[item.class?.(item.value), item.color?.(item.value)]"
          >
            {{ item.value }}
          </span>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";
import { CustomerContact, CustomerResourceSymbol } from "@/types";
import { HDCustomerMember } from "@/types/doctypes";
import { getErrorMessage, hasPermission } from "@/utils";
import { Avatar, Badge, Button, Dropdown, Tooltip, dayjs } from "frappe-ui";
import { computed, inject, markRaw } from "vue";
import LucideBriefcase from "~icons/lucide/briefcase";
import LucideMail from "~icons/lucide/mail";
import LucideMoreHorizontal from "~icons/lucide/more-horizontal";
import LucidePhone from "~icons/lucide/phone";
import LucideTicket from "~icons/lucide/ticket";
import ModifiedIcon from "../icons/ModifiedIcon.vue";

const props = defineProps<{
  contact: CustomerContact;
}>();
const emit = defineEmits(["update"]);
const { $dialog } = globalStore();
const customer = inject(CustomerResourceSymbol)!;

const ticketCountLabel = computed(() => {
  const count = props.contact.ticket_count;
  if (count === 0) return __("No open tickets");
  return `${count} ${count === 1 ? __("ticket") : __("tickets")}`;
});

function findPrimaryContact(): HDCustomerMember | undefined {
  return customer.doc.contacts?.find((c) => c.is_primary === 1);
}

const contactDetails = computed(() => [
  {
    icon: markRaw(LucideMail),
    value: props.contact.email_id || "-",
  },
  {
    icon: markRaw(LucidePhone),
    value: props.contact.mobile_no || "-",
  },
  {
    icon: markRaw(ModifiedIcon),
    value: `Updated ${dayjs(props.contact.modified).fromNow()}`,
  },
  {
    icon: markRaw(LucideTicket),
    value: ticketCountLabel.value,
    color: (value: string) =>
      value !== __("No open tickets") ? "!text-amber-700" : "!text-ink-gray-7",
    class: (value: string) =>
      value !== __("No open tickets") ? "hover:underline cursor-pointer" : "",
  },
]);

const dropdownOptions = computed(() => {
  const options = [];
  if (!props.contact.is_primary) {
    options.push({
      label: __("Set as Primary"),
      icon: "star",
      onClick: () => {
        /* TODO: set as primary action */
        console.log("Set as primary");
        updatePrimaryContact(1);
      },
    });
  }
  if (props.contact.is_manager) {
    options.push({
      label: __("Revoke Manager Access"),
      icon: "user-x",
      theme: "red",
      onClick: () => {
        /* TODO: remove manager action */
        updateManagerRole(0);
      },
    });
  } else {
    options.push({
      label: __("Set as Manager"),
      icon: "briefcase",
      onClick: () => {
        /* TODO: set as manager action */
        updateManagerRole(1);
      },
    });
  }
  options.push({
    label: __("Remove Contact"),
    icon: "x",
    theme: "red",
    onClick: () => {
      /* TODO: remove contact action */
      removeContact();
    },
  });
  return options;
});

function updateManagerRole(isManager: 0 | 1) {
  const contact = customer.doc.contacts?.find(
    (c) => c.contact_name === props.contact.contact_name
  ) as HDCustomerMember | undefined;
  if (!contact) return;

  contact.is_manager = isManager;
  customer.setValue.submit(
    {
      contacts: customer.doc.contacts,
    },
    {
      onSuccess() {
        emit("update");
      },
      onError(error: any) {
        getErrorMessage(error, true);
      },
    }
  );
}

function updatePrimaryContact(isPrimary: 0 | 1) {
  // find the contact with is_primary = 1 and set it to 0
  const primaryContact = findPrimaryContact();
  if (primaryContact) {
    primaryContact.is_primary = 0;
  }
  // find the current contact and set it to 1
  const currentContact = customer.doc.contacts?.find(
    (c) => c.contact_name === props.contact.contact_name
  ) as HDCustomerMember | undefined;
  if (!currentContact) return;
  // if both same return
  if (currentContact.is_primary === isPrimary) return;
  currentContact.is_primary = isPrimary;
  customer.setValue.submit(
    {
      contacts: customer.doc.contacts,
    },
    {
      onSuccess() {
        emit("update");
      },
      onError(error: any) {
        getErrorMessage(error, true);
      },
    }
  );
}

function removeContact() {
  // remove the current contact from the contacts array
  customer.doc.contacts = customer.doc.contacts?.filter(
    (c) => c.contact_name !== props.contact.contact_name
  );
  customer.setValue.submit(
    {
      contacts: customer.doc.contacts,
    },
    {
      onSuccess() {
        emit("update");
      },
      onError(error: any) {
        getErrorMessage(error, true);
      },
    }
  );
}
</script>

<style scoped></style>
