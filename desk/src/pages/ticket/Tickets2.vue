<template>
  <div>
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <RouterLink
          :to="{ name: isCustomerPortal ? 'TicketNew' : 'TicketAgentNew' }"
        >
          <Button label="Create" theme="gray" variant="solid">
            <template #prefix>
              <LucidePlus class="h-4 w-4" />
            </template>
          </Button>
        </RouterLink>
      </template>
    </LayoutHeader>
    <ListViewBuilder
      :options="options"
      @row-click="
        (row) =>
          $router.push({
            name: isCustomerPortal ? 'TicketCustomer' : 'TicketAgent',
            params: { ticketId: row },
          })
      "
    />
  </div>
</template>

<script setup lang="ts">
import { h } from "vue";
import { Breadcrumbs, Badge, Tooltip } from "frappe-ui";
import { dayjs } from "@/dayjs";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { LayoutHeader, ListViewBuilder } from "@/components";
import { IndicatorIcon } from "@/components/icons";
import { isCustomerPortal } from "@/utils";

const { textColorMap } = useTicketStatusStore();

const breadcrumbs = [
  {
    label: "Tickets",
    route: {
      name: isCustomerPortal.value ? "TicketsCustomer" : "TicketsAgent",
    },
  },
];

const options = {
  doctype: "HD Ticket",
  columnConfig: {
    status: {
      prefix: ({ row }) => {
        return h(IndicatorIcon, {
          class: textColorMap[row.status],
        });
      },
    },
    agreement_status: {
      custom: ({ item }) => {
        return h(Badge, {
          label: item,
          theme: slaStatusColorMap[item],
          variant: "outline",
        });
      },
    },
    response_by: {
      custom: ({ row, item }) => handle_response_by_field(row, item),
    },
    resolution_by: {
      custom: ({ row, item }) => handle_resolution_by_field(row, item),
    },
  },
};

function handle_response_by_field(row: any, item: string) {
  if (!row.first_responded_on && dayjs(item).isBefore(new Date())) {
    return h(Badge, {
      label: "Failed",
      theme: "red",
      variant: "outline",
    });
  }
  if (row.first_responded_on && dayjs(row.first_responded_on).isBefore(item)) {
    return h(Badge, {
      label: "Fulfilled",
      theme: "green",
      variant: "outline",
    });
  } else if (dayjs(row.first_responded_on).isAfter(item)) {
    return h(Badge, {
      label: "Failed",
      theme: "red",
      variant: "outline",
    });
  } else {
    return h(
      Tooltip,
      {
        text: dayjs(item).long(),
      },
      () => dayjs.tz(item).fromNow()
    );
  }
}

function handle_resolution_by_field(row: any, item: string) {
  if (row.resolution_date && dayjs(row.resolution_date).isBefore(item)) {
    return h(Badge, {
      label: "Fulfilled",
      theme: "green",
      variant: "outline",
    });
  } else if (dayjs(row.resolution_date).isAfter(item)) {
    return h(Badge, {
      label: "Failed",
      theme: "red",
      variant: "outline",
    });
  } else {
    return h(
      Tooltip,
      {
        text: dayjs(item).long(),
      },
      () => dayjs.tz(item).fromNow()
    );
  }
}

const slaStatusColorMap = {
  Fulfilled: "green",
  Failed: "red",
  "Resolution Due": "orange",
  "First Response Due": "orange",
  Paused: "blue",
};
</script>
