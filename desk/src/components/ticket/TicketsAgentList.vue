<template>
  <ListView
    v-if="rows.length"
    class="px-5"
    :columns="columns"
    :rows="rows"
    :options="{
      getRowRoute: (row) => ({
        name: 'TicketAgent',
        params: { ticketId: row.name },
      }),
      selectable: options.selectable,
      showTooltip: false,
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
        <div
          v-if="column.key === '_assign'"
          class="flex items-center"
          @click="(e) => handleFieldClick(e, column.key, item)"
        >
          <MultipleAvatar :avatars="item" />
        </div>
        <ListRowItem
          v-else
          :item="item"
          class="text-base text-gray-700"
          @click="(e) => handleFieldClick(e, column.key, item)"
        >
          <template #prefix>
            <div v-if="column.key === 'status'">
              <IndicatorIcon :class="ticketStatusStore.textColorMap[item]" />
            </div>
          </template>
          <div v-if="column.key === 'agreement_status'">
            <Badge
              v-if="item"
              :label="item"
              :theme="slaStatusColorMap[item]"
              variant="outline"
            />
          </div>
          <div v-if="column.type === 'Rating'">
            <StarRating :rating="item" />
          </div>
          <div v-else-if="column.key === 'response_by'">
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
              {{ dayjs.tz(item).fromNow() }}
            </Tooltip>
          </div>
          <div v-else-if="column.key === 'resolution_by'">
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
              {{ dayjs.tz(item).fromNow() }}
            </Tooltip>
          </div>
          <div v-else-if="column.key === 'creation'">
            {{ dayjs.tz(item).fromNow() }}
          </div>
          <div v-else-if="column.key === 'modified'">
            {{ dayjs.tz(item).fromNow() }}
          </div>
        </ListRowItem>
      </ListRow>
    </ListRows>
    <ListSelectBanner>
      <template #actions="{ selections }">
        <Dropdown
          :options="[
            {
              group: 'Options',
              hideLabel: true,
              items: [
                {
                  label: 'Export',
                  icon: () =>
                    h(FeatherIcon, { name: 'download', class: 'h-4 w-4' }),
                  onClick: () => {
                    selectedRows = selections;
                    showExportDialog = true;
                  },
                },
              ],
            },
          ]"
        >
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
      </template>
    </ListSelectBanner>
  </ListView>
  <div v-else class="flex h-full items-center justify-center">
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <TicketIcon class="h-10 w-10" />
      <span>No Tickets Found</span>
    </div>
  </div>
  <ListFooter
    v-if="rows.length && paginate"
    v-model="pageLength"
    class="bottom-0 border-t px-5 py-2"
    :options="{ rowCount: options.rowCount, totalCount: options.totalCount }"
    @update:model-value="emit('update:pageLength', $event)"
    @load-more="emit('update:pageLength', 'loadMore')"
  />
  <Dialog
    v-model="showExportDialog"
    :options="{
      title: 'Export',
      actions: [
        {
          label: 'Download',
          variant: 'solid',
          onClick: () => {
            emit('event:export', {
              export_type: export_type,
              export_all: export_all,
              selections: Array.from(selectedRows).join(','),
            });
            showExportDialog = false;
            export_type = 'Excel';
            export_all = false;
          },
        },
      ],
    }"
  >
    <template #body-content>
      <FormControl
        v-model="export_type"
        variant="outline"
        :label="'Export Type'"
        type="select"
        :options="[
          {
            label: 'Excel',
            value: 'Excel',
          },
          {
            label: 'CSV',
            value: 'CSV',
          },
        ]"
        :placeholder="'Excel'"
      />
      <div class="mt-3">
        <FormControl
          v-model="export_all"
          type="checkbox"
          :label="`Export All ${options.totalCount} Record(s)`"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { dayjs } from "@/dayjs";
import { ref, h } from "vue";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { TicketIcon } from "@/components/icons";
import {
  ListView,
  ListRows,
  ListRow,
  ListRowItem,
  ListHeader,
  ListFooter,
  ListSelectBanner,
  FeatherIcon,
  Dropdown,
} from "frappe-ui";
import { MultipleAvatar, StarRating } from "@/components";

const ticketStatusStore = useTicketStatusStore();
const showExportDialog = ref(false);
const export_type = ref("Excel");
const export_all = ref(false);
let selectedRows;

const props = defineProps({
  columns: {
    type: Array, //TODO custom types
    required: true,
  },
  rows: {
    type: Array,
    required: true,
  },
  colFieldType: {
    type: Object,
    default: () => ({}),
  },
  pageLength: {
    type: Number,
    default: 20,
  },
  paginate: {
    type: Boolean,
    default: true,
  },
  options: {
    type: Object,
    default: () => ({
      totalCount: 0,
      rowCount: 0,
      selectable: true,
    }),
  },
});

let emit = defineEmits([
  "update:pageLength",
  "event:fieldClick",
  "event:export",
]);
let pageLength = ref(props.pageLength);

function handleFieldClick(e, name: string, value: string | [string]) {
  if (
    props.colFieldType[name] === "Link" ||
    props.colFieldType[name] === "Select" ||
    name === "_assign"
  ) {
    e.preventDefault();
    if (name === "_assign") {
      if (value.length > 1) {
        let target = e.target.closest(".user-avatar");
        if (target) {
          value = target.getAttribute("data-name");
        }
      } else {
        value = value[0].name;
      }
    }
    emit("event:fieldClick", {
      name,
      type: props.colFieldType[name],
      value,
    });
  }
}

//TODO: move all constants to relevant composables
const slaStatusColorMap = {
  Fulfilled: "green",
  Failed: "red",
  "Resolution Due": "orange",
  "First Response Due": "orange",
  Paused: "blue",
};
</script>
