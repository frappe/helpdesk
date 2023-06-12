<template>
  <Tooltip :text="name">
    <Avatar size="sm" :image="image" :label="name" />
  </Tooltip>
</template>

<script>
import { Avatar } from "frappe-ui";

export default {
  name: "AgentAvatar",
  components: {
    Avatar,
  },
  props: {
    agent: {
      type: String,
      default: "",
    },
  },
  computed: {
    user() {
      return this.$resources?.user?.doc || {};
    },
    image() {
      return this.user.user_image;
    },
    name() {
      return this.user.full_name;
    },
  },
  resources: {
    user() {
      if (!this.agent) return;

      return {
        type: "document",
        doctype: "User",
        name: this.agent,
        cache: ["User", this.agent],
      };
    },
  },
};
</script>
