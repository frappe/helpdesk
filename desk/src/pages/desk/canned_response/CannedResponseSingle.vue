<template>
  <div class="flex flex-col">
    <CannedResponseInfo
      class="shrink-0 border-r border-[#F4F5F6]"
      :canned_response="id"
    />
  </div>
</template>

<script>
import CannedResponseInfo from "@/components/desk/settings/canned_responses/CannedResponseInfo.vue";
export default {
  name: "CannedResponse",
  components: {
    CannedResponseInfo,
  },
  props: ["id"],
  mounted() {
    this.$event.emit("set-selected-setting", "Canned Responses");
    this.$event.emit("show-top-panel-actions-settings", "CannedResponse");
  },
};
</script>
