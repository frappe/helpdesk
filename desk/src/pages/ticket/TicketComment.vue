<template>
  <div class="my-4 rounded border bg-cyan-50 p-4">
    <div class="mb-4 flex items-center justify-between">
      <div class="flex items-center gap-0.5 text-base">
        <UserAvatar v-bind="user" size="lg" expand strong />
        <Icon icon="lucide:dot" class="text-gray-500" />
        <Tooltip :text="dayjs(date).long()">
          <div class="text-gray-600">
            {{ dayjs(date).fromNow() }}
          </div>
        </Tooltip>
        <Icon v-if="isPinned" icon="lucide:dot" class="text-gray-500" />
        <Badge v-if="isPinned" label="Pinned" theme="blue" variant="outline" />
      </div>
      <div class="flex items-center gap-1">
        <Badge label="Comment" theme="green" variant="outline" />
        <Dropdown :options="options">
          <template #default>
            <Button theme="gray" variant="ghost">
              <template #icon>
                <Icon icon="lucide:more-horizontal" />
              </template>
            </Button>
          </template>
        </Dropdown>
      </div>
    </div>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <span class="prose-f" v-html="content"></span>
  </div>
</template>

<script setup lang="ts">
import { toRefs, h, computed } from "vue";
import { createResource, Badge, Button, Dropdown, Tooltip } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { dayjs } from "@/dayjs";
import { emitter } from "@/emitter";
import { createToast } from "@/utils";
import { useAuthStore } from "@/stores/auth";
import { UserInfo } from "@/types";
import { UserAvatar } from "@/components";

interface P {
  content: string;
  date: string;
  isPinned: number;
  name: string;
  user: UserInfo;
}

const props = defineProps<P>();
const { content, name, isPinned, user } = toRefs(props);
const authStore = useAuthStore();
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
      isHidden: user.value.email !== authStore.userId,
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
