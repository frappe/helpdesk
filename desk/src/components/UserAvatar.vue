<template>
  <div class="flex items-center gap-2">
    <Avatar
      v-if="user"
      :label="user?.full_name"
      :image="user?.user_image"
      v-bind="$attrs"
    />
    <span v-if="expand">
      {{ user?.full_name }}
    </span>
  </div>
</template>
<script setup lang="ts">
import { computed } from "vue";
import { Avatar } from "frappe-ui";
import { useUserStore } from "@/stores/user";

interface P {
  user?: string;
  expand?: boolean;
}

const props = withDefaults(defineProps<P>(), {
  user: "",
  expand: false,
});
const { getUser } = useUserStore();
const user = computed(() => getUser(props.user));
</script>
