<template>
  <div class="flex items-center gap-2">
    <Avatar
      :label="user?.full_name || props.user"
      :image="user?.user_image"
      v-bind="$attrs"
    />
    <span v-if="expand" class="text-base font-medium text-gray-900">
      {{ user?.full_name || props.user }}
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
