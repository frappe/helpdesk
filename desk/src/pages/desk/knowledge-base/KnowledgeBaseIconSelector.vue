<template>
  <Popover>
    <template #target="{ togglePopover }">
      <Button @click="togglePopover">
        <template #icon>
          <component :is="getIcon(icon)" />
        </template>
      </Button>
    </template>
    <template #body-main="{ togglePopover }">
      <div class="grid grid-cols-6 gap-2 p-2">
        <Button
          v-for="i in icons"
          :key="i"
          class="place-self-center"
          @click="
            () => {
              emit('select', i);
              togglePopover();
            }
          "
        >
          <template #icon>
            <component :is="getIcon(i)" />
          </template>
        </Button>
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import { Popover } from "frappe-ui";
import { getIcon } from "./util";
import { icons } from "./data";

interface P {
  icon: string;
}

interface E {
  (event: "select", icon: string): void;
}

defineProps<P>();
const emit = defineEmits<E>();
</script>
