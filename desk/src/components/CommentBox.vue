<template>
  <div class="flex-col text-base">
    <div class="mb-0.5 flex items-center justify-between">
      <div class="text-gray-600">
        <span class="font-medium text-gray-800">
          {{ commenter }}
        </span>
        <span> added a</span>
        <span class="max-w-xs truncate font-medium text-gray-800">
          comment
        </span>
        <span class="px-1">&middot;</span>
        <Tooltip :text="dateFormat(creation, dateTooltipFormat)">
          <span class="pl-0.5 text-sm">
            {{ timeAgo(creation) }}
          </span>
        </Tooltip>
      </div>
      <div v-if="authStore.userId === commenter" class="px-4">
        <Dropdown
          :options="[
            { label: 'Delete', onClick: () => deleteComment.submit() },
          ]"
        >
          <Button
            icon="more-horizontal"
            class="text-gray-600"
            variant="ghost"
          />
        </Dropdown>
      </div>
    </div>
    <div
      class="prose-f grow cursor-pointer rounded bg-gray-50 px-4 py-3 text-base leading-6 transition-all duration-300 ease-in-out"
      v-html="content"
    />
  </div>
</template>

<script setup lang="ts">
import { Dropdown, createResource } from "frappe-ui";
import { dateFormat, timeAgo, dateTooltipFormat, createToast } from "@/utils";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const props = defineProps({
  name: {
    type: String,
    required: true,
  },
  creation: {
    type: String,
    required: true,
  },
  content: {
    type: String,
    required: true,
  },
  commenter: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["update"]);

const deleteComment = createResource({
  url: "frappe.client.delete",
  makeParams: () => ({
    doctype: "HD Ticket Comment",
    name: props.name,
  }),
  onSuccess() {
    emit("update");
    createToast({
      title: "Comment deleted",
      icon: "check",
      iconClasses: "text-green-500",
    });
  },
});
</script>
