<template>
  <ListView
    class="px-5"
    :columns="columns"
    :rows="rows"
    :options="{
      getRowRoute: (row) => ({
        name: 'TicketAgent',
        params: { ticketId: row.name },
      }),
      selectable: true,
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
          @click="(e) => handleFieldClick(e, column.key, item)"
        >
          <MultipleAvatar :avatars="[item]" />
        </div>
        <ListRowItem
          v-else
          :item="item"
          :class="['text-base', { 'text-3xl font-semibold text-gray-900': checkCondition(row), 'text-gray-600': !checkCondition(row) }]"
          @click="(e) => handleFieldClick(e, column.key, item)"
        >
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
          <div v-if="column.key === 'agreement_status'">
            <Badge
              v-if="item"
              :label="item"
              :theme="slaStatusColorMap[item]"
              variant="outline"
            />
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
            {{ get_time_zone(item) }}
          </div>
          <div v-else-if="column.key === 'modified'">
            {{ dayjs.tz(item).fromNow() }}
          </div>
        </ListRowItem>
      </ListRow>
    </ListRows>
  </ListView>
  <ListFooter
    v-model="pageLength"
    class="bottom-0 border-t px-5 py-2"
    :options="{ rowCount: options.rowCount, totalCount: options.totalCount }"
    @update:model-value="emit('update:pageLength', $event)"
    @load-more="emit('update:pageLength', 'loadMore')"
  />
</template>



<script setup lang="ts">
import {
  ListView,
  ListRows,
  ListRow,
  ListRowItem,
  ListHeader,
  ListFooter,
  createResource
} from "frappe-ui";
import { MultipleAvatar } from "@/components";
import { dayjs } from "@/dayjs";
import { ref } from "vue";
import { useUserStore } from "@/stores/user";
import momentTimezone from "moment-timezone/builds/moment-timezone-with-data-10-year-range.min.js";

const userStore = useUserStore();
const UserDetails = userStore.users.data

function handleFieldClick(e, name: string, value: string) {
  if (
    props.colFieldType[name] === "Link" ||
    props.colFieldType[name] === "Select" ||
    name === "_assign"
  ) {
    e.preventDefault();
    if (name === "_assign") {
      value = value.name;
    }
    emit("event:fieldClick", {
      name,
      type: props.colFieldType[name],
      value,
    });
  }
}
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
    required: true,
  },
  pageLength: {
    type: Number,
    required: true,
    default: 20,
  },
  options: {
    type: Object,
    default: () => ({
      totalCount: 0,
      rowCount: 0,
    }),
  },
  name: {
    type: String,
    required: true,
  },
});
const user = userStore.getUser(props.name);

let pageLength = ref(props.pageLength);
let emit = defineEmits(["update:pageLength", "event:fieldClick"]);

const slaStatusColorMap = {
  Fulfilled: "green",
  Failed: "red",
  "Resolution Due": "orange",
  "First Response Due": "orange",
  Paused: "blue",
};

const DefaultTimezone = 'Asia/Riyadh';
const momentTz = {}

function get_time_zone(timeSelected: string){
  UserDetails.forEach(d=> {
    if(d.email == user.email){
      momentTz['date'] = momentTimezone
        .tz(timeSelected, 'YYYY/MM/DD HH:mm', DefaultTimezone)
        .tz(d.time_zone)
        .format('YYYY/MM/DD HH:mm');
      }
  })
  return momentTz['date']
}
// function convert_date(originalTimestamp: string) {
//   const dateObj = new Date(originalTimestamp);
//   const formattedDate = ${dateObj.getFullYear()}-${(dateObj.getMonth() + 1).toString().padStart(2, '0')}-${dateObj.getDate().toString().padStart(2, '0')} ${dateObj.getHours().toString().padStart(2, '0')}:${dateObj.getMinutes().toString().padStart(2, '0')}:${dateObj.getSeconds().toString().padStart(2, '0')};
//   return formattedDate;
// }

function checkCondition(row) {  
  return !row._seen.includes(user.email);
}
</script>
