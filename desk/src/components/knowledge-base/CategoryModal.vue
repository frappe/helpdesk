<template>
  <Dialog
    v-model:open="showDialog"
    :title="dialogTitle"
    :actions="getActionButton()"
  >
    <template #default>
      <div class="flex flex-col flex-1 gap-4">
        <div>
          <div class="mb-1.5 text-base text-ink-gray-5">{{ __("Name") }}</div>
          <textarea
            class="text-base rounded-4 py-1.5 px-2 border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-elevation-2 hover:bg-surface-gray-3 focus:bg-surface-base focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors w-full block"
            ref="titleRef"
            placeholder="Support Issues"
            v-model="newTitle"
            :rows="1"
            maxlength="50"
            autofocus
            @input="(e: Event) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = `${target.scrollHeight}px`;
            }"
          />
        </div>
        <div>
          <div class="mb-1.5 text-base text-ink-gray-5">{{ __("Icon") }}</div>
          <Combobox
            class="w-full"
            v-model="icon"
            :options="iconOptions"
            :placeholder="__('Select an icon')"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Combobox, Dialog } from "frappe-ui";
import { CATEGORY_ICONS } from "@helpdesk/shared/categoryIcons";
import { __ } from "@/translation";
import { ref } from "vue";
import { watch } from "vue";

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
const icon = defineModel<string>("icon");

const iconOptions = CATEGORY_ICONS.map((value) => ({
  value,
  icon: value,
  label: value
    .replace("lucide-", "")
    .replace(/-/g, " ")
    .replace(/^\w/, (c) => c.toUpperCase()),
}));

const dialogTitle = computed(() =>
  props.edit ? "Edit Category" : "Create Category"
);

const titleRef = ref(null);
watch(
  () => titleRef.value,
  (newVal) => {
    if (!newVal) return;
    titleRef.value.style.height =
      newVal.scrollHeight > newVal.clientHeight
        ? newVal.scrollHeight + "px"
        : newVal.scrollHeight + "px";
  }
);

function getActionButton() {
  const action = [];
  if (props.edit) {
    action.push({
      label: "Save",
      variant: "solid",
      onClick: () => {
        emit("update");
      },
    });
  } else {
    action.push({
      label: "Create",
      variant: "solid",
      onClick: () => {
        emit("create");
      },
    });
  }
  return action;
}
</script>
