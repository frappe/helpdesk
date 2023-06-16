<template>
  <div class="group flex gap-3">
    <div class="flex w-8 justify-end">
      <Avatar :image="sender.user_image" :label="sender.full_name" size="sm" />
    </div>
    <div class="flex w-full flex-col gap-1.5">
      <div class="flex items-start justify-between">
        <div class="flex items-center">
          <div class="text-base text-gray-900">{{ sender.full_name }}</div>
          <IconDot class="text-gray-600" />
          <div class="text-sm text-gray-600">{{ dateDisplay }}</div>
        </div>
        <Dropdown v-if="!isEmpty(options)" :options="options">
          <template #default>
            <FeatherIcon
              name="more-horizontal"
              class="h-5 w-5 cursor-pointer opacity-0 group-hover:opacity-100"
            />
          </template>
        </Dropdown>
      </div>
      <div
        class="prose prose-p:m-0 max-w-none rounded-lg bg-gray-100 p-2 text-base text-gray-700"
      >
        <!-- This is vulnerable to attacks. Prefer markdown wherever possible. -->
        <!-- eslint-disable-next-line vue/no-v-html -->
        <span v-html="content"></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PropType, ref, toRefs } from "vue";
import { createResource, Avatar, Dropdown, FeatherIcon } from "frappe-ui";
import { isEmpty } from "lodash";
import dayjs from "dayjs";
import { useAuthStore } from "@/stores/auth";
import { createToast } from "@/utils/toasts";
import IconDot from "~icons/ph/dot-bold";

type Sender = {
  name: string;
  full_name: string;
  user_image: string;
};

const props = defineProps({
  content: {
    type: String,
    required: true,
  },
  date: {
    type: String,
    required: true,
  },
  name: {
    type: String,
    required: true,
  },
  sender: {
    type: Object as PropType<Sender>,
    required: true,
  },
});
const { content, date, name, sender } = toRefs(props);
const authStore = useAuthStore();
const dateDisplay = dayjs(date.value).format("h:mm A");
const options = ref([]);

function deleteComment() {
  createResource({
    url: "frappe.client.delete",
    params: {
      doctype: "HD Ticket Comment",
      name: name.value,
    },
    auto: true,
    onSuccess() {
      createToast({
        title: "Comment deleted",
        icon: "check",
        iconClasses: "text-green-500",
      });
    },
  });
}

if (sender.value.name === authStore.userId) {
  options.value.push({
    label: "Delete",
    onClick: () => deleteComment(),
  });
}
</script>
