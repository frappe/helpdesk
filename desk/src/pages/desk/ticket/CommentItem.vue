<template>
  <div class="group flex gap-3">
    <div class="flex w-8 justify-end">
      <Avatar :image="user?.user_image" :label="user?.full_name" size="sm" />
    </div>
    <div class="flex w-full flex-col gap-1.5">
      <div class="flex items-start justify-between">
        <div class="flex items-center">
          <div class="text-base text-gray-900">
            {{ user?.full_name }}
          </div>
          <Icon icon="lucide:dot" class="text-gray-600" />
          <Tooltip :text="dateExtended">
            <div class="text-xs text-gray-600">
              {{ dateDisplay }}
            </div>
          </Tooltip>
          <div v-if="isPinned" class="flex items-center gap-1">
            <Icon icon="lucide:dot" class="text-gray-600" />
            <IconPin class="h-3 w-3 text-gray-700" />
          </div>
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
        <!-- eslint-disable-next-line vue/no-v-html -->
        <span v-html="content"></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { toRefs, h, computed } from "vue";
import {
  createResource,
  Avatar,
  Dropdown,
  FeatherIcon,
  Tooltip,
} from "frappe-ui";
import { isEmpty } from "lodash";
import dayjs from "dayjs";
import { Icon } from "@iconify/vue";
import { emitter } from "@/emitter";
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
import { createToast } from "@/utils/toasts";

interface P {
  content: string;
  date: string;
  isPinned: number;
  name: string;
  sender: string;
}

const props = defineProps<P>();
const { content, date, name, sender, isPinned } = toRefs(props);
const authStore = useAuthStore();
const userStore = useUserStore();
const user = userStore.getUser(sender.value);
const dateDisplay = dayjs(date.value).fromNow();
const dateExtended = dayjs(date.value).format("dddd, MMMM D, YYYY h:mm A");
const IconTrash = h(Icon, { icon: "lucide:trash-2" });
const IconPin = h(Icon, { icon: "lucide:pin" });
const IconUnpin = h(Icon, { icon: "lucide:pin-off" });
const options = computed(() =>
  [
    {
      label: isPinned.value ? "Unpin" : "Pin",
      icon: isPinned.value ? IconUnpin : IconPin,
      onClick: () => togglePin.submit(),
    },
    {
      label: "Delete",
      icon: IconTrash,
      onClick: () => deleteComment.submit(),
      isHidden: sender.value !== authStore.userId,
    },
  ].filter((i) => !i.isHidden)
);

const togglePin = createResource({
  url: "frappe.client.set_value",
  makeParams: () => ({
    doctype: "HD Ticket Comment",
    name: name.value,
    fieldname: "is_pinned",
    value: !isPinned.value,
  }),
  onSuccess: () => emitter.emit("update:ticket"),
});

const deleteComment = createResource({
  url: "frappe.client.delete",
  makeParams: () => ({
    doctype: "HD Ticket Comment",
    name: name.value,
  }),
  onSuccess() {
    emitter.emit("update:ticket");
    createToast({
      title: "Comment deleted",
      icon: "check",
      iconClasses: "text-green-500",
    });
  },
});
</script>
