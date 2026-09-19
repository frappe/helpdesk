<template>
  <LayoutHeader>
    <template #left-header>
      <div class="flex max-w-[60%] flex-col truncate">
        <Breadcrumbs :items="breadcrumbs" class="breadcrumbs -ms-0.5">
          <template #prefix="{ item }">
            <Icon
              v-if="item.icon"
              :icon="item.icon"
              class="me-1 h-4 flex items-center justify-center self-center"
            />
          </template>
        </Breadcrumbs>
      </div>
    </template>
    <template #right-header>
      <div class="flex gap-2 items-center">
        <MultipleAvatar
          :avatars="JSON.stringify(viewers)"
          size="md"
          :hide-name="true"
        />
        <!-- Custom Actions -->
        <div v-if="normalActions.length" class="flex gap-2">
          <Button v-for="action in normalActions" v-bind="action">
            <template v-if="action.icon" #prefix>
              <Icon :icon="action.icon" class="h-4 w-4" />
            </template>
          </Button>
        </div>
        <div v-if="groupedWithLabelActions.length">
          <div v-for="g in groupedWithLabelActions" :key="g.label">
            <Dropdown v-slot="{ open }" :options="g.action">
              <Button :label="__(g.label)">
                <template #suffix>
                  <component
                    :is="open ? LucideChevronUp : LucideChevronDown"
                    class="h-4"
                  />
                </template>
              </Button>
            </Dropdown>
          </div>
        </div>
        <!-- Status -->
        <Dropdown :options="statusDropdown" align="end">
          <template #default="{ open }">
            <Button :label="__(ticket.doc.status)" ref="statusRef">
              <template #prefix>
                <IndicatorIcon
                  :class="
                    ticketStatusStore.getStatus(ticket.doc.status)?.parsed_color
                  "
                />
              </template>
            </Button>
          </template>
        </Dropdown>
        <!-- Core Actions + Custom Actions -->
        <Dropdown
          v-if="groupedActions.length"
          :options="groupedActions"
          align="end"
        >
          <Button icon="lucide-more-horizontal" />
        </Dropdown>
      </div>
    </template>
  </LayoutHeader>
  <TicketMergeModal
    :ticket="ticket.doc"
    v-if="showMergeModal"
    v-model="showMergeModal"
    @update="ticket.reload()"
  />
  <TicketSubjectModal v-model="showSubjectDialog" />
</template>

<script setup lang="ts">
import LucideChevronUp from "~icons/lucide/chevron-up";
import LucideChevronDown from "~icons/lucide/chevron-down";
import Icon from "@/components/Icon.vue";
import { MultipleAvatar } from "@/components";
import LayoutHeader from "@/components/LayoutHeader.vue";
import TicketMergeModal from "@/components/ticket/TicketMergeModal.vue";
import { showMergeModal } from "@/pages/ticket/modalStates";
import {
  createToast,
  setupCustomizations,
} from "@/composables/formCustomisation";
import { useNotifyTicketUpdate } from "@/composables/realtime";
import { useShortcut } from "@/composables/shortcuts";
import { useView } from "@/composables/useView";
import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { __ } from "@/translation";
import { CustomizationSymbol, TicketSymbol, View } from "@/types";
import { HDTicketStatus } from "@/types/doctypes";
import { getIcon } from "@/utils";
import {
  Breadcrumbs,
  Button,
  call,
  createResource,
  Dropdown,
  toast,
} from "frappe-ui";
import {
  computed,
  ComputedRef,
  h,
  inject,
  onMounted,
  PropType,
  ref,
  useTemplateRef,
  watchEffect,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import LucideMerge from "~icons/lucide/merge";
import { IndicatorIcon } from "../icons";
import TicketSubjectModal from "./TicketSubjectModal.vue";
const { isAdmin } = useAuthStore();
const { $dialog } = globalStore();

defineProps({
  viewers: {
    type: Array as PropType<string[]>,
    required: true,
  },
});

const route = useRoute();
const router = useRouter();
const { findView } = useView("HD Ticket");
const ticketStatusStore = useTicketStatusStore();

const ticket = inject(TicketSymbol)!;
const customizations = inject(CustomizationSymbol)!;
const showSubjectDialog = ref(false);

const { notifyTicketUpdate } = useNotifyTicketUpdate(ticket.value?.name);
const statusDropdown = computed(() => {
  const statuses =
    ticketStatusStore.statuses.data?.filter((s) => s.enabled) || [];
  return statuses.map((o: HDTicketStatus) => ({
    label: __(o.label_agent),
    value: o.label_agent,
    onClick: () => {
      if (ticket.value.doc.status === o.label_agent) return;

      if (o.label_agent === "Closed") {
        confirmCloseTicket();
        return;
      }

      updateTicketStatus(o.label_agent);
    },
    icon: () =>
      h(IndicatorIcon, {
        class: o.parsed_color,
      }),
  }));
});
const breadcrumbs = computed(() => {
  let items = [{ label: __("Tickets"), route: { name: "TicketsAgent" } }];
  if (route.query.view) {
    const currView: ComputedRef<View> = findView(route.query.view as string);
    if (currView) {
      items.push({
        label: __(currView.value?.label),
        icon: getIcon(currView.value?.icon),
        route: { name: "TicketsAgent", query: { view: currView.value?.name } },
      });
    }
  }
  items.push({
    label: ticket.value.doc?.subject,
    onClick: () => {
      showSubjectDialog.value = true;
    },
  });
  return items;
});

function updateField(fieldname: string, value: string, callback = () => {}) {
  const doc = ticket.value;
  doc.setValue.submit({
    [fieldname]: value,
  });
  callback();
}

function handleDeleteTicket() {
  $dialog({
    title: __(`Delete ticket #${ticket?.value?.name}`),
    message: __(
      "Are you sure you want to delete this ticket? This is an irreversible action and cannot be undone."
    ),
    actions: [
      {
        label: __("Delete"),
        theme: "red",
        iconLeft: "lucide-trash-2",
        variant: "solid",
        onClick({ close }) {
          call("helpdesk.api.ticket.delete_ticket", {
            name: ticket?.value?.doc.name,
          })
            .then(() => {
              toast.success(__("Ticket deleted successfully."));
              router.push({ name: "TicketsAgent" });
            })
            .catch((err: any) => {
              toast.error(err || __("Failed to delete ticket."));
            });
          close();
        },
      },
    ],
  });
}

const ticketCount = createResource({
  url: "frappe.client.get_count",
  makeParams: () => ({
    doctype: "HD Ticket",
    filters: {
      status_category: ["!=", "Resolved"],
      is_merged: 0,
    },
  }),
  auto: true,
});
const showMergeOption = computed(() => {
  return (
    !ticket?.value?.doc?.is_merged &&
    ["Open", "Paused"].includes(ticket?.value?.doc?.status_category) &&
    ticketCount.data > 1
  );
});
const defaultActions = computed(() => {
  let items = [];

  if (showMergeOption.value) {
    items.push({
      label: __("Merge Ticket"),
      icon: LucideMerge,
      condition: () => !ticket.value.doc.is_merged,
      onClick: () => (showMergeModal.value = true),
    });
  }

  return [
    {
      group: __("Default actions"),
      hideLabel: true,
      options: items,
    },
  ];
});

const deleteAction = computed(() => {
  if (!isAdmin) return [];
  return [
    {
      group: __("Default actions"),
      hideLabel: true,
      options: [
        {
          label: __("Delete"),
          icon: "lucide-trash-2",
          theme: "red",
          onClick: handleDeleteTicket,
        },
      ],
    },
  ];
});

const actions = ref<any[]>([]);
const normalActions = computed(() => {
  return actions.value.filter((action) => !action.group);
});

const groupedWithLabelActions = computed(() => {
  let _actions = [];

  actions.value
    .filter((action) => action.buttonLabel && action.group)
    .forEach((action) => {
      let groupIndex = _actions.findIndex(
        (a) => a.label === action.buttonLabel
      );
      if (groupIndex > -1) {
        _actions[groupIndex].action.push(action);
      } else {
        _actions.push({
          label: __(action.buttonLabel),
          action: [action],
        });
      }
    });
  return _actions;
});

const groupedActions = computed(() => {
  let _actions = [];
  _actions = _actions.concat(defaultActions.value);
  _actions = _actions.concat(
    actions.value.filter((action) => action.group && !__(action.buttonLabel))
  );
  _actions = _actions.concat(deleteAction.value);
  // Drop empty groups so the kebab hides when there is nothing to show. Form
  // script actions are flat rows with no `options`, so they must survive.
  return _actions.filter((action) => !action.options || action.options.length);
});

const customizationCtx = computed(() => ({
  doc: ticket?.value?.doc,
  call,
  router,
  toast,
  $dialog: globalStore().$dialog,
  updateField,
  createToast,
}));

// to manage the correct  customization context for actions, happens because of navigation between tickets using buttons
watchEffect(async () => {
  if (customizations.value?.data) {
    await setupCustomizations(
      customizations.value.data,
      customizationCtx.value
    );

    actions.value = [...(customizations.value?.data?._customActions || [])];
  }
});

const statusRef = useTemplateRef("statusRef");

onMounted(() => {
  useShortcut("s", () => {
    statusRef.value?.$el?.click();
  });
});
const hasAgentCommunication = computed(() => {
  return activities.value?.data?.communications?.some(
    (communication) => communication.sent_or_received === "Sent"
  );
});

function updateTicketStatus(status: string) {
  notifyTicketUpdate("Status", status);

  if (ticket.value.doc.status === status) return;

  ticket.value.setValue.submit(
    { status },
    {
      onSuccess() {
        activities.value.reload();
      },
    }
  );
}

function confirmCloseTicket() {
  $dialog({
    title: __("Close Ticket"),
    message: hasAgentCommunication.value
      ? __("Are you sure you want to close this ticket?")
      : __("Are you sure you want to close this ticket without resolution?"),
    actions: [
      {
        label: __("Confirm"),
        variant: "solid",
        onClick({ close }) {
          updateTicketStatus("Closed");
          close();
        },
      },
    ],
  });
}
</script>

<style>
.breadcrumbs button {
  background-color: inherit !important;
  &:hover,
  &:focus {
    background-color: inherit !important;
  }
}
</style>
