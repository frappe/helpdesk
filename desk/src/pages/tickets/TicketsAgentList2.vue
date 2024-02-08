<template>
  <ListView
    :columns="columns"
    :rows="rows"
    :options="{
      getRowRoute: (row) => ({
        name: 'TicketAgent2',
        params: { ticketId: row.name },
      }),
      selectable: true,
      showTooltip: true,
    }"
    row-key="name"
  >
    <ListHeader />
    <ListRows>
      <ListRow
        v-for="row in rows"
        :key="row.name"
        v-slot="{ column, item }"
        :row="row"
      >
        <ListRowItem :item="item" class="text-base text-gray-700">
          <template #prefix>
            <div v-if="column.key === 'status'">
              <IndicatorIcon v-if="item == 'Open'" class="text-red-600" />
              <IndicatorIcon
                v-else-if="item == 'Replied'"
                class="text-blue-600"
              />
              <IndicatorIcon
                v-else-if="item == 'Resolved'"
                class="text-green-700"
              />
              <IndicatorIcon v-else class="text-gray-700" />
            </div>
          </template>
          <div v-if="column.key === 'response_by'">
            <Badge
              v-if="
                row.first_responded_on &&
                dayjs(row.first_responded_on).isBefore(item)
              "
              label="Fulfilled"
              theme="green"
              variant="outline"
            />
            <Badge
              v-else-if="dayjs(row.first_responded_on).isAfter(item)"
              label="Failed"
              theme="red"
              variant="outline"
            />
            <Tooltip v-else :text="dayjs(item).long()">
              {{ dayjs(item).fromNow() }}
            </Tooltip>
          </div>
          <div v-if="column.key === 'resolution_by'">
            <Badge
              v-if="
                row.resolution_date && dayjs(row.resolution_date).isBefore(item)
              "
              label="Fulfilled"
              theme="green"
              variant="outline"
            />
            <Badge
              v-else-if="dayjs(row.resolution_date).isAfter(item)"
              label="Failed"
              theme="red"
              variant="outline"
            />
            <Tooltip v-else :text="dayjs(item).long()">
              {{ dayjs(item).fromNow() }}
            </Tooltip>
          </div>
          <div v-if="column.key === 'agreement_status'">
            <Badge
              v-if="item"
              :label="item"
              :theme="slaStatusColorMap[item]"
              variant="outline"
            />
          </div>
          <div v-if="column.key === 'creation'">
            {{ dayjs(item).fromNow() }}
          </div>
          <div v-if="column.key === 'modified'">
            {{ dayjs(item).fromNow() }}
          </div>
        </ListRowItem>
      </ListRow>
    </ListRows>
  </ListView>
  <!-- <ListFooter
    v-if="true"
    class="border-t px-5 py-2"
    v-model="pageLengthCount"
    :options="{
      rowCount: 20,
      totalCount: 100,
    }"
    @loadMore="true"
  /> -->
</template>

<script setup lang="ts">
import {
  ListView,
  ListRows,
  ListRow,
  ListRowItem,
  ListHeader,
  // ListFooter,
} from "frappe-ui";
import { dayjs } from "@/dayjs";

defineProps({
  columns: {
    type: Array, //TODO custom types
    required: true,
  },
  rows: {
    type: Array,
    required: true,
  },
});

const slaStatusColorMap = {
  Fulfilled: "green",
  Failed: "red",
  "Resolution Due": "orange",
  "First Response Due": "orange",
  Paused: "blue",
};
</script>
