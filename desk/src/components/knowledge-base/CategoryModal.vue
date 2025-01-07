<template>
  <Dialog v-model="showDialog" :options="{ title: dialogTitle }">
    <template #body-content>
      <div class="flex flex-col flex-1 gap-3">
        <FormControl
          v-model="newTitle"
          type="textarea"
          size="sm"
          variant="subtle"
          :disabled="false"
        />
        <Button
          variant="solid"
          label="Save"
          @click="emit('update')"
          v-if="edit"
        />
        <Button variant="solid" label="Create" @click="emit('create')" v-else />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Dialog } from "frappe-ui";

const props = defineProps({
  title: {
    type: String,
    default: "",
  },
  edit: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update", "create"]);

const showDialog = defineModel<boolean>();
const newTitle = defineModel<string>("title");

const dialogTitle = computed(() =>
  props.edit ? "Edit Category" : "Create Category"
);
</script>

<style scoped></style>
