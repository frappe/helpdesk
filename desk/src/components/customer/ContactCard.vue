<template>
  <div
    class="rounded-md bg-surface-white border border-outline-gray-1 px-3 py-2.5 flex flex-col gap-2.5 hover:border-outline-gray-3 hover:cursor-pointer"
    @click="goToContact"
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
          :class="contact.is_manager ? 'max-w-[50%]' : ''"
        >
          {{ contact.contact_name }}
        </p>
        <Tooltip
          v-if="contact.is_manager"
          :text="__('Can view tickets raised by all contacts of the customer.')"
          placement="top"
        >
          <Badge :label="__('Manager')" theme="green" variant="outline" />
        </Tooltip>
      </div>
      <div class="flex gap-1">
        <Tooltip
          v-if="contact.is_primary"
          :text="__('Primary')"
          placement="top"
        >
          <span
            class="flex h-6 w-6 items-center justify-center text-ink-amber-2"
            :aria-label="__('Primary')"
          >
            <LucideStar class="size-4 fill-ink-amber-2" />
          </span>
        </Tooltip>
        <Dropdown
          v-if="hasPermission()"
          placement="right"
          :options="dropdownOptions"
        >
          <Button
            class="h-6 w-6 p-0 min-w-fit shrink-0"
            variant="ghost"
            @click.stop
          >
            <LucideMoreHorizontal class="h-4 w-4 text-ink-gray-6" />
          </Button>
        </Dropdown>
      </div>
    </div>
    <div class="border-t border-gray-200 w-full" />
    <div class="flex flex-col gap-3">
      <template v-for="item in contactDetails" :key="item.value">
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
import {
  Avatar,
  Badge,
  Button,
  Dropdown,
  Tooltip,
  dayjs,
  toast,
} from "frappe-ui";
import { computed, inject, markRaw } from "vue";
import { useRouter } from "vue-router";
import LucideMail from "~icons/lucide/mail";
import LucideMoreHorizontal from "~icons/lucide/more-horizontal";
import LucidePhone from "~icons/lucide/phone";
import LucideStar from "~icons/lucide/star";
import LucideTicket from "~icons/lucide/ticket";
import ModifiedIcon from "../icons/ModifiedIcon.vue";

const props = defineProps<{
  contact: CustomerContact;
}>();
const emit = defineEmits(["update"]);
const router = useRouter();

const { $dialog } = globalStore();
const customer = inject(CustomerResourceSymbol)!;

const ticketCountLabel = computed(() => {
  const count = props.contact.ticket_count;
  if (count === 0) return __("No active tickets");
  return `${count} ${count === 1 ? __("active ticket") : __("active tickets")}`;
});

function goToContact() {
  router.push({ name: "Contact", params: { id: props.contact.contact_name } });
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
    value: `Last seen ${
      props.contact.last_active
        ? dayjs(props.contact.last_active).fromNow()
        : "Never"
    }`,
  },
  {
    icon: markRaw(LucideTicket),
    value: ticketCountLabel.value,
    color: (value: string) =>
      value !== __("No active tickets")
        ? "!text-amber-700"
        : "!text-ink-gray-4",
    class: (value: string) =>
      value !== __("No active tickets") ? "hover:underline cursor-pointer" : "",
  },
]);

const dropdownOptions = computed(() => {
  const primaryActions = [];
  if (!props.contact.is_primary) {
    primaryActions.push({
      label: __("Set as Primary"),
      icon: "star",
      onClick: () => {
        updatePrimaryContact();
      },
    });
  }
  const roleActions = [
    {
      label: __("Role"),
      icon: "briefcase",
      submenu: [
        {
          label: __("Customer"),
          icon: props.contact.is_manager ? undefined : "check",
          onClick: () => {
            if (!props.contact.is_manager) return;
            updateManagerRole(0);
          },
        },
        {
          label: __("Customer Manager"),
          icon: props.contact.is_manager ? "check" : undefined,
          onClick: () => {
            if (props.contact.is_manager) return;
            updateManagerRole(1);
          },
        },
      ],
    },
  ];

  const destructiveActions = [
    {
      label: __("Remove Contact"),
      icon: "x",
      theme: "red" as const,
      onClick: () => {
        removeContact();
      },
    },
  ];
  const deleteActionGroup = {
    group: "",
    hideLabel: true,
    items: destructiveActions,
  };

  if (props.contact.is_primary) {
    return [deleteActionGroup];
  }

  return [
    {
      group: "",
      hideLabel: true,
      items: [...primaryActions, ...roleActions],
    },
    deleteActionGroup,
  ];
});

function updateManagerRole(isManager: 0 | 1) {
  const title = isManager
    ? __("Grant Manager Access")
    : __("Revoke Manager Access");
  const message = isManager
    ? __(
        "They'll get access to tickets raised by everyone in the organisation."
      )
    : __("They'll only see their own tickets going forward.");

  $dialog({
    title,
    message,
    actions: [
      {
        label: __("Confirm"),
        variant: "solid",
        onClick: ({ close }: { close: () => void }) => {
          const contact = customer.doc.contacts?.find(
            (c) => c.contact_name === props.contact.contact_name
          ) as HDCustomerMember | undefined;
          if (!contact) return;

          contact.is_manager = isManager;
          customer.setValue.submit(
            { contacts: customer.doc.contacts },
            {
              onSuccess() {
                emit("update");
                close();
                toast.success(__("Role updated successfully"));
              },
              onError(error: any) {
                getErrorMessage(error, true);
              },
            }
          );
        },
      },
    ],
  });
}

function updatePrimaryContact() {
  if (customer.doc.primary_contact === props.contact.contact_name) return;

  $dialog({
    title: __("Set Primary Contact"),
    message: __(
      "This contact will become the primary point of contact and will be able to view tickets raised by all other contacts in the organisation."
    ),
    actions: [
      {
        label: __("Confirm"),
        variant: "solid",
        onClick: ({ close }: { close: () => void }) =>
          customer.setValue.submit(
            { primary_contact: props.contact.contact_name },
            {
              onSuccess() {
                emit("update");
                close();
                toast.success(__("Primary contact updated"));
              },
              onError(error: any) {
                getErrorMessage(error, true);
              },
            }
          ),
      },
    ],
  });
}

function removeContact() {
  $dialog({
    title: __("Remove Contact"),
    message: __(
      "Are you sure you want to remove this contact from the customer?"
    ),
    actions: [
      {
        label: __("Confirm"),
        variant: "solid",
        onClick: ({ close }: { close: () => void }) =>
          customer.setValue.submit(
            {
              contacts: customer.doc.contacts?.filter(
                (c) => c.contact_name !== props.contact.contact_name
              ),
            },
            {
              onSuccess() {
                emit("update");
                close();
                toast.success(__("Contact removed successfully"));
              },
              onError(error: any) {
                getErrorMessage(error, true);
              },
            }
          ),
      },
    ],
  });
}
</script>
