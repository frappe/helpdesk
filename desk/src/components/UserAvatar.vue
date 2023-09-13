<template>
  <div class="flex items-center gap-2">
    <Avatar
      :label="user?.full_name || props.user"
      :image="image || user?.user_image"
      v-bind="$attrs"
    />
    <span
      v-if="expand"
      class="truncate"
      :class="{
        'text-gray-900': strong,
        'font-medium': strong,
      }"
    >
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
  image?: string;
  expand?: boolean;
  strong?: boolean;
}

const props = withDefaults(defineProps<P>(), {
  user: "",
  image: "",
  expand: false,
  strong: false,
});
const { getUser } = useUserStore();
const user = computed(() => getUser(props.user));
</script>
