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
          @click="showCallLogModal = true"
        >
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
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
      v-model:callLog="callLog"
    />
    <CallLogModal
      v-model="showCallLogModal"
      :data="callLog?.data"
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
import {
  Avatar,
  Badge,
  Button,
  createResource,
  FeatherIcon,
  usePageMeta,
} from "frappe-ui";
import { computed, h, ref } from "vue";
import CallLogDetailModal from "./CallLogDetailModal.vue";
import CallLogModal from "./CallLogModal.vue";
import { statusColorMap } from "./utils";

const showCallLogModal = ref(false);
const showCallLogDetailModal = ref(false);
const callLog = ref(null);

const listViewRef = ref(null);

const options = computed(() => {
  return {
    doctype: "TF Call Log",
    selectable: true,
    showSelectBanner: true,
    emptyState: {
      title: "No Call Logs Found",
    },
    columnConfig: {
      caller: {
        prefix: ({ row }) => {
          return h(Avatar, {
            shape: "circle",
            image: row.caller || "Unknown",
            label: row.caller || "Unknown",
            size: "sm",
          });
        },
        custom: ({ row }) => {
          return h("span", row.caller || "Unknown");
        },
      },
      receiver: {
        prefix: ({ row }) => {
          return h(Avatar, {
            shape: "circle",
            image: row.receiver || "Unknown",
            label: row.receiver || "Unknown",
            size: "sm",
          });
        },
        custom: ({ row }) => {
          return h("span", row.receiver || "Unknown");
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
            label: row.status,
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

function openCallLog(id: string): void {
  showCallLogDetailModal.value = true;
  callLog.value = createResource({
    url: "telephony.api.get_call_log",
    params: { name: id },
    cache: ["call_log", id],
    auto: true,
  });
}

usePageMeta(() => {
  return {
    title: "Call Logs",
  };
});
</script>
