<template>
  <Tooltip v-if="user" :text="getTooltipLabel(user.full_name)">
    <Avatar :image="user.user_image" :label="user.full_name" size="sm" />
  </Tooltip>
</template>

<script setup lang="ts">
import { computed, toRef } from "vue";
import { Avatar, Tooltip } from "frappe-ui";
import { useUserStore } from "@/stores/user";

type P = {
  assign?: string;
};

const userStore = useUserStore();
const props = withDefaults(defineProps<P>(), {
  assign: "",
});

const assign = toRef(props, "assign");
const assignJson = computed(() => JSON.parse(assign.value));
const agent = computed(() => [...assignJson.value].pop());
const user = computed(() => userStore.getUser(agent.value));

function getTooltipLabel(s: string) {
  return "Assigned to " + s;
}
</script>
