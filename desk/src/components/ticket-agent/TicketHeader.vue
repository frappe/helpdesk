<template>
  <LayoutHeader>
    <template #left-header>
      <div class="flex flex-col truncate">
        <Breadcrumbs :items="breadcrumbs" class="breadcrumbs">
          <template #prefix="{ item }">
            <Icon
              v-if="item.icon"
              :icon="item.icon"
              class="mr-1 h-4 flex items-center justify-center self-center"
            />
          </template>
        </Breadcrumbs>
        <TicketSLA />
      </div>
    </template>
    <template #right-header>
      <div class="flex gap-2 items-center">
        <MultipleAvatar
          :avatars="JSON.stringify(viewers)"
          size="md"
          :hide-name="true"
        />
        <!-- Navigation -->
        <TicketNavigation :key="ticket.name" />
        <!-- Custom Actions -->
        <div v-if="normalActions.length" class="flex gap-2">
          <Button
            v-for="action in normalActions"
            :key="action.label"
            :label="action.label"
            @click="action.onClick()"
          >
            <template v-if="action.icon" #prefix>
              <FeatherIcon :name="action.icon" class="h-4 w-4" />
            </template>
          </Button>
        </div>
        <div v-if="groupedWithLabelActions.length">
          <div v-for="g in groupedWithLabelActions" :key="g.label">
            <Dropdown v-slot="{ open }" :options="g.action">
              <Button :label="g.label">
                <template #suffix>
                  <FeatherIcon
                    :name="open ? 'chevron-up' : 'chevron-down'"
                    class="h-4"
                  />
                </template>
              </Button>
            </Dropdown>
          </div>
        </div>
        <!-- Status -->
        <Dropdown :options="statusDropdown" placement="right">
          <template #default="{ open }">
            <Button :label="ticket.doc.status">
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
          placement="right"
        >
          <Button icon="more-horizontal" />
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
  <TicketSubjectModal v-if="showSubjectDialog" v-model="showSubjectDialog" />
</template>

<script setup lang="ts">
import { MultipleAvatar } from "@/components";
import LayoutHeader from "@/components/LayoutHeader.vue";
import TicketMergeModal from "@/components/ticket/TicketMergeModal.vue";
import { setupCustomizations } from "@/composables/formCustomisation";
import { useNotifyTicketUpdate } from "@/composables/realtime";
import { useView } from "@/composables/useView";
import { globalStore } from "@/stores/globalStore";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import {
  ActivitiesSymbol,
  CustomizationSymbol,
  TicketSymbol,
  View,
} from "@/types";
import { HDTicketStatus } from "@/types/doctypes";
import { getIcon } from "@/utils";
import { Breadcrumbs, call, Dropdown, toast } from "frappe-ui";
import {
  computed,
  ComputedRef,
  h,
  inject,
  PropType,
  ref,
  watchEffect,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import LucideMerge from "~icons/lucide/merge";
import { IndicatorIcon } from "../icons";
import TicketNavigation from "./TicketNavigation.vue";
import TicketSLA from "./TicketSLA.vue";
import TicketSubjectModal from "./TicketSubjectModal.vue";

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

const ticket = inject(TicketSymbol);
const customizations = inject(CustomizationSymbol);
const activities = inject(ActivitiesSymbol);

const showSubjectDialog = ref(false);

const { notifyTicketUpdate } = useNotifyTicketUpdate(ticket.value?.name);
const statusDropdown = computed(() => {
  const statuses =
    ticketStatusStore.statuses.data?.filter((s) => s.enabled) || [];
  return statuses.map((o: HDTicketStatus) => ({
    label: o.label_agent,
    value: o.label_agent,
    onClick: () => {
      notifyTicketUpdate("Status", o.label_agent);
      if (ticket.value.doc.status === o.label_agent) return;
      ticket.value.setValue.submit(
        { status: o.label_agent },
        {
          onSuccess() {
            activities.value.reload();
          },
        }
      );
    },
    icon: () =>
      h(IndicatorIcon, {
        class: o.parsed_color,
      }),
  }));
});
const breadcrumbs = computed(() => {
  let items = [{ label: "Tickets", route: { name: "TicketsAgent" } }];
  if (route.query.view) {
    const currView: ComputedRef<View> = findView(route.query.view as string);
    if (currView) {
      items.push({
        label: currView.value?.label,
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

const showMergeModal = ref(false);
const showMergeOption = computed(() => {
  return (
    !ticket.value.doc.is_merged &&
    ["Open", "Paused"].includes(ticket.value.doc.status_category)
  );
});
const defaultActions = computed(() => {
  let items = [];

  if (showMergeOption.value) {
    items.push({
      label: "Merge Ticket",
      icon: LucideMerge,
      condition: () => !ticket.value.doc.is_merged,
      onClick: () => (showMergeModal.value = true),
    });
  }
  // items.push({
  //   label: "Jump to ticket",
  //   icon: LucideTicket,
  //   onClick: () => {
  //     console.log("HELLO");
  //   },
  // });
  return [
    {
      group: "Default actions",
      hideLabel: true,
      items,
    },
  ];
});
const actions = ref([]);
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
          label: action.buttonLabel,
          action: [action],
        });
      }
    });
  return _actions;
});

const groupedActions = computed(() => {
  let _actions = [];
  _actions = _actions.concat(
    actions.value.filter((action) => action.group && !action.buttonLabel)
  );
  return _actions;
});

const customizationCtx = computed(() => ({
  doc: ticket?.value?.doc,
  call,
  router,
  toast,
  $dialog: globalStore().$dialog,
  updateField,
  createToast: toast.create,
}));

// to manage the correct  customization context for actions, happens because of navigation between tickets using buttons
watchEffect(async () => {
  if (customizations.value?.data) {
    await setupCustomizations(
      customizations.value.data,
      customizationCtx.value
    );

    actions.value = [
      ...defaultActions.value,
      ...(customizations.value?.data?._customActions || []),
    ];
  }
});
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
