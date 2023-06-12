<template>
  <div class="flex flex-col">
    <TeamInfo :team-id="teamId" />
  </div>
</template>

<script>
import TeamInfo from "@/components/desk/settings/teams/TeamInfo.vue";
export default {
  name: "Team",
  components: {
    TeamInfo,
  },
  props: ["teamId"],
  setup() {},
  mounted() {
    this.$event.emit("set-selected-setting", "Teams");
  },
};
</script>
