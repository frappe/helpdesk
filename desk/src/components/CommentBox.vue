<template>
  <div class="flex-col text-base">
    <div class="mb-1 ml-0.5 flex items-center justify-between">
      <div class="text-gray-600 flex items-center gap-2">
        <Avatar
          size="sm"
          :label="commenter"
          :image="getUser(commentedBy).user_image"
        />
        <p>
          <span class="font-medium text-gray-800">
            {{ commenter }}
          </span>
          <span> added a</span>
          <span class="max-w-xs truncate font-medium text-gray-800">
            comment
          </span>
        </p>
      </div>
      <div class="flex items-center">
        <Tooltip :text="dateFormat(creation, dateTooltipFormat)">
          <span class="pl-0.5 text-sm text-gray-600">
            {{ timeAgo(creation) }}
          </span>
        </Tooltip>
        <div v-if="authStore.userId === commentedBy">
          <Dropdown
            :options="[{ label: 'Delete', onClick: () => (showDialog = true) }]"
          >
            <Button
              icon="more-horizontal"
              class="text-gray-600"
              variant="ghost"
            />
          </Dropdown>
        </div>
      </div>
    </div>
    <div
      class="prose-f grow cursor-pointer rounded bg-gray-50 px-4 py-3 text-base leading-6 transition-all duration-300 ease-in-out"
      v-html="content"
    />
  </div>
  <Dialog
    v-model="showDialog"
    :options="{
      title: 'Delete Comment',
      message: 'Are you sure you want to confirm this action?',
      actions: [
        { label: 'Cancel', onClick: () => (showDialog = false) },
        {
          label: 'Delete',
          onClick: () => deleteComment.submit(),
          variant: 'solid',
        },
      ],
    }"
  />
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Dropdown, createResource, Dialog, Avatar } from "frappe-ui";
import { dateFormat, timeAgo, dateTooltipFormat, createToast } from "@/utils";
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";

const authStore = useAuthStore();
const props = defineProps({
  activity: {
    type: Object,
    required: true,
  },
});
const { getUser } = useUserStore();

const { name, creation, content, commenter, commentedBy } = props.activity;

const emit = defineEmits(["update"]);
const showDialog = ref(false);

const deleteComment = createResource({
  url: "frappe.client.delete",
  makeParams: () => ({
    doctype: "HD Ticket Comment",
    name: name,
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
