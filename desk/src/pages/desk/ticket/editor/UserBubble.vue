<template>
  <div
    class="flex items-center gap-1 rounded-md bg-gray-100 px-2 py-1 text-sm text-gray-800"
  >
    <Avatar :image="image || user?.user_image" :label="name" size="sm" />
    {{ name }}
  </div>
</template>

<script setup lang="ts">
import { Avatar } from "frappe-ui";
import { useUserStore } from "@/stores/user";
import { computed, toRef } from "vue";

interface P {
  name: string;
  image?: string;
}

const props = withDefaults(defineProps<P>(), {
  image: null,
});

const name = toRef(props, "name");
const userStore = useUserStore();
const user = computed(() => userStore.getUser(name.value));
</script>
