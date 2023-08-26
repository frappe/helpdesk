<template>
  <Tooltip v-if="user" :text="getTooltipLabel(userName)">
    <Avatar :image="userImage" :label="userName" />
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
const assignJson = computed(() => {
  const parsed = JSON.parse(assign.value);
  const arr = Array.isArray(parsed) ? parsed : [];
  return arr;
});
const agent = computed(() => [...assignJson.value].pop());
const user = computed(() => userStore.getUser(agent.value));
const userImage = computed(() => user.value?.user_image);
const userName = computed(() => user.value?.full_name);

function getTooltipLabel(s: string) {
  return "Assigned to " + s;
}
</script>
