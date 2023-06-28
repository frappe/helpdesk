<template>
  <Tooltip v-if="agent" :text="getTooltipLabel(user.doc?.full_name)">
    <Avatar
      size="sm"
      :label="user.doc?.full_name"
      :image="user.doc?.user_image"
    />
  </Tooltip>
</template>

<script setup lang="ts">
import { computed, defineProps, toRef } from "vue";
import { createDocumentResource, Avatar, Tooltip } from "frappe-ui";

const props = defineProps({
  assign: {
    type: String,
    required: false,
    default: "",
  },
});

const assign = toRef(props, "assign");
const assignJson = computed(() => JSON.parse(assign.value));
const agent = computed(() => [...assignJson.value].pop());
const user = createDocumentResource({
  doctype: "User",
  name: agent.value,
  auto: true,
  cache: ["User", agent.value],
});

function getTooltipLabel(s: string) {
  return "Assigned to " + s;
}
</script>
