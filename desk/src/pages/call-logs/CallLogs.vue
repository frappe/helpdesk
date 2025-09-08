<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Call Logs</div>
      </template>
      <template #right-header>
        <Button
          label="New Call Log"
          theme="gray"
          variant="solid"
          @click="newCallLog"
          icon-left="plus"
        />
      </template>
    </LayoutHeader>
    <ListViewBuilder
      ref="listViewRef"
      :options="options"
      @row-click="openCallLog"
      @empty-state-action="showCallLogModal = true"
    />
    <CallLogDetailModal
      v-model="showCallLogDetailModal"
      v-model:callLogModal="showCallLogModal"
      :callLogId="callLogId"
    />
    <CallLogModal
      v-model="showCallLogModal"
      :callLogId="callLogId"
      @after-insert="
        () => {
          listViewRef?.reload();
        }
      "
    />
  </div>
</template>

<script setup lang="ts">
import LayoutHeader from "@/components/LayoutHeader.vue";
import ListViewBuilder from "@/components/ListViewBuilder.vue";
import { Avatar, Badge, Button, FeatherIcon, usePageMeta } from "frappe-ui";
import { computed, h, ref } from "vue";
import CallLogDetailModal from "./CallLogDetailModal.vue";
import CallLogModal from "./CallLogModal.vue";
import { statusColorMap, statusLabelMap } from "./utils";
import { PhoneIcon } from "@/components/icons";

const showCallLogModal = ref(false);
const showCallLogDetailModal = ref(false);
const callLogId = ref("");

const listViewRef = ref(null);

const options = computed(() => {
  return {
    doctype: "TP Call Log",
    selectable: true,
    showSelectBanner: true,
    emptyState: {
      title: "No Call Logs Found",
      icon: PhoneIcon,
    },
    columnConfig: {
      caller: {
        prefix: ({ row }) => {
          return h(Avatar, {
            shape: "circle",
            image: row._caller?.image || "Unknown",
            label: row._caller?.label || "Unknown",
            size: "sm",
          });
        },
        custom: ({ row }) => {
          return h("span", row._caller?.label || "Unknown");
        },
      },
      receiver: {
        prefix: ({ row }) => {
          return h(Avatar, {
            shape: "circle",
            image: row._receiver?.image || "Unknown",
            label: row._receiver?.label || "Unknown",
            size: "sm",
          });
        },
        custom: ({ row }) => {
          return h("span", row._receiver?.label || "Unknown");
        },
      },
      type: {
        prefix: ({ row }) => {
          let icon =
            row.type === "Incoming" ? "phone-incoming" : "phone-outgoing";
          return h(FeatherIcon, {
            name: icon,
            class: ["size-3 shrink-0"],
          });
        },
      },
      status: {
        custom: ({ row }) => {
          return h(Badge, {
            label: statusLabelMap[row.status],
            variant: "subtle",
            theme: statusColorMap[row.status],
          });
        },
      },
      duration: {
        prefix: () => {
          return h(FeatherIcon, {
            name: "clock",
            class: ["size-3 shrink-0"],
          });
        },
        custom: ({ row }) => {
          return h("span", row.duration ? row.duration + "s" : "0s");
        },
      },
    },
  };
});

const newCallLog = () => {
  callLogId.value = "";
  showCallLogModal.value = true;
};

function openCallLog(id: string): void {
  callLogId.value = id;
  showCallLogDetailModal.value = true;
}

usePageMeta(() => {
  return {
    title: "Call Logs",
  };
});
</script>
