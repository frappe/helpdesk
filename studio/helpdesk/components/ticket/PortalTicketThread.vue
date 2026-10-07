<template>
  <TicketEmails
    :key="ticket"
    :ticket="ticket"
    :extra-activities="extraActivities"
    :version="version"
  >
    <template v-for="(_, name) in $slots" #[name]="scope">
      <slot :name="name" v-bind="scope || {}" />
    </template>
  </TicketEmails>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, watch, type PropType } from "vue";
import { dayjs } from "frappe-ui";
import {
  ActivityTimeline,
  useActivityTimeline,
} from "@framework/ui/components/ActivityTimeline";

type Row = { timestamp?: string };

// A component, not the page script: the composable needs a component's setup.
defineProps<{
  ticket: string;
  // The page's own rows, such as closes; merged in by time.
  extraActivities?: Row[];
  // The ticket's `modified`, so a save reloads the emails.
  version?: string;
}>();

// Keyed by the ticket above: the composable reads its ticket once, so another ticket remounts it.
const TicketEmails = defineComponent({
  props: {
    ticket: { type: String, required: true },
    extraActivities: { type: Array as PropType<Row[]>, default: () => [] },
    version: String,
  },
  setup(props, { slots }) {
    const { activities, loading, paginate, reload } = useActivityTimeline(
      "HD Ticket",
      props.ticket,
      ["email"]
    );
    watch(
      () => props.version,
      (_, before) => before && reload()
    );
    // A customer never sees who else an email went to.
    const rows = computed(() =>
      [
        ...activities.value.map((row) => ({
          ...row,
          data: { ...row.data, to: "", cc: "", bcc: "" },
        })),
        ...props.extraActivities,
      ].sort(
        (first, second) =>
          dayjs(first.timestamp).valueOf() - dayjs(second.timestamp).valueOf()
      )
    );
    return () =>
      h(
        ActivityTimeline,
        { activities: rows.value, loading: loading.value, paginate },
        slots
      );
  },
});
</script>
