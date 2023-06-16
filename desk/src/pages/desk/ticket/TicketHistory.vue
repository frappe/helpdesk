<template>
  <div class="flex flex-col border-l">
    <div class="flex items-center justify-between p-4">
      <div class="text-lg font-semibold text-gray-800">Ticket history</div>
      <Button
        icon="x"
        theme="gray"
        variant="ghost"
        @click="sidebar.isExpanded = false"
      />
    </div>
    <div class="overflow-auto px-4">
      <ol class="relative border-l border-gray-200 text-base">
        <li
          v-for="activity in activities"
          :key="activity.name"
          class="mb-4 ml-4"
        >
          <IconDot class="absolute -left-3 h-6 w-6 bg-white text-gray-500" />
          <div class="mb-1 font-medium text-gray-900 first-letter:capitalize">
            {{ activity.action }}
          </div>
          <Tooltip :text="activity.dateLong">
            <div class="text-gray-700 first-letter:capitalize">
              {{ activity.dateShort }}
            </div>
          </Tooltip>
        </li>
      </ol>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ComputedRef } from "vue";
import { Button, createListResource, Tooltip } from "frappe-ui";
import dayjs from "dayjs";
import { useTicketStore } from "./data";
import IconDot from "~icons/ph/dot-bold";

class Activity {
  constructor(
    public name: string,
    public action: string,
    public creation: string,
    public owner: string
  ) {}

  get dayjsInstance() {
    return dayjs(this.creation).tz(dayjs.tz.guess());
  }

  get dateLong() {
    // https://day.js.org/docs/en/display/format
    return this.dayjsInstance.format("dddd, MMMM D, YYYY h:mm A");
  }

  get dateShort() {
    return this.dayjsInstance.fromNow();
  }
}

const { sidebar, ticket } = useTicketStore();

const r = createListResource({
  doctype: "HD Ticket Activity",
  fields: ["name", "creation", "action", "owner"],
  filters: {
    ticket: ticket.doc.name,
  },
  orderBy: "creation desc",
  auto: true,
});

const activities: ComputedRef<Array<Activity>> = computed(
  () =>
    r.data?.map(
      (a: Activity) => new Activity(a.name, a.action, a.creation, a.owner)
    ) || []
);
</script>
