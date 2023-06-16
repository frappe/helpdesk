<template>
  <Dialog v-model="keymapStore.isOpen" :options="options">
    <template #body-content>
      <div v-if="!isEmpty(keymapStore.items)" class="space-y-2">
        <div
          v-for="item in keymapStore.items"
          :key="item.keyCombination.join()"
          class="flex items-center justify-between"
        >
          <div class="text-base">
            {{ item.help }}
          </div>
          <div class="flex gap-1">
            <Badge
              v-for="key in item.display"
              :key="key"
              :label="key"
              theme="gray"
              variant="outline"
              size="lg"
            />
          </div>
        </div>
      </div>
      <div v-else class="text-gray-700">No shortcuts defined</div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { Badge } from "frappe-ui";
import { isEmpty } from "lodash";
import { useKeymapStore } from "@/stores/keymap";

const keymapStore = useKeymapStore();
const options = {
  title: "Shortcuts",
};
</script>
