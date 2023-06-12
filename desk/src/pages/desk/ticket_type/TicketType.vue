<template>
  <div class="flex flex-col">
    <TicketTypeInfo :ticket-type-id="id" />
  </div>
</template>

<script>
import TicketTypeInfo from "@/components/desk/settings/ticket_types/TicketTypeInfo.vue";
export default {
  name: "TicketType",
  components: {
    TicketTypeInfo,
  },
  props: ["id"],
  mounted() {
    this.$event.emit("set-selected-setting", "Ticket Types");
  },
};
</script>
