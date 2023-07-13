<template>
  <div class="flex flex-col overflow-hidden">
    <TopBar
      :back-to="{ name: AGENT_PORTAL_KNOWLEDGE_BASE }"
      :title="article.data?.title"
    >
      <template #right>
        <div class="flex gap-2">
          <Button
            :label="bLabel"
            theme="gray"
            variant="solid"
            @click="bClick"
          />
          <Dropdown :options="dOptions">
            <Button theme="gray" variant="ghost">
              <template #icon>
                <IconMoreHorizontal class="h-4 w-4" />
              </template>
            </Button>
          </Dropdown>
        </div>
      </template>
    </TopBar>
    <div class="overflow-auto">
      <div
        class="my-8 mx-auto"
        :style="{
          width: '742px',
        }"
      >
        <div class="mb-8 flex items-center gap-1.5">
          <div class="text-base text-gray-600">
            {{ article.data?.category.category_name }}
          </div>
          <IconChevronRight class="h-3 w-3 text-gray-600" />
          <div class="text-base text-gray-800">
            {{ article.data?.sub_category.category_name }}
          </div>
        </div>
        <div class="mb-4.5 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Avatar
              :label="article.data?.author.full_name"
              :image="article.data?.author.user_image"
            />
            <div class="text-base text-gray-800">
              {{ article.data?.author.full_name }}
            </div>
            <IconDot class="h-4 w-4 text-gray-600" />
            <div class="text-xs text-gray-800">
              {{ dateFormatted }}
            </div>
          </div>
          <div class="flex items-center gap-2 text-gray-600">
            <IconThumbsUp class="h-4 w-4" />
            <div class="text-base">
              {{ article.data?.helpful }}
            </div>
            <div class="text-base text-gray-300">|</div>
            <IconThumbsDown class="h-4 w-4" />
            <div class="text-base">
              {{ article.data?.not_helpful }}
            </div>
          </div>
        </div>
        <div class="border-b pb-3 text-3xl font-semibold text-gray-900">
          {{ article.data?.title }}
        </div>
        <div
          class="prose-sm my-4 max-w-none"
          v-html="article.data?.content"
        ></div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed } from "vue";
import { createResource, debounce, Avatar, Button, Dropdown } from "frappe-ui";
import dayjs from "dayjs";
import { AGENT_PORTAL_KNOWLEDGE_BASE } from "@/router";
import { createToast } from "@/utils/toasts";
import TopBar from "@/components/TopBar.vue";
import IconChevronRight from "~icons/lucide/chevron-right";
import IconDot from "~icons/lucide/dot";
import IconMoreHorizontal from "~icons/lucide/more-horizontal";
import IconThumbsDown from "~icons/lucide/thumbs-down";
import IconThumbsUp from "~icons/lucide/thumbs-up";
import IconEdit from "~icons/lucide/edit-3";
import IconTrash from "~icons/lucide/trash-2";

const article = createResource({
  url: "helpdesk.helpdesk.doctype.hd_article.api.get_article",
  params: {
    name: "de99e3d725",
  },
  auto: true,
});

const dateFormatted = computed(() =>
  dayjs(article.data?.creation).format("MMMM D, YYYY")
);

const setValueRes = createResource({
  url: "frappe.client.set_value",
  onSuccess() {
    article.reload();
  },
  onError(error) {
    const msg = error.messages.join(", ");
    createToast({
      title: "Error updating article",
      text: msg,
      icon: "x",
      iconClasses: "text-red-500",
    });
  },
});

const publish = debounce(() => {
  setValueRes.submit({
    doctype: "HD Article",
    name: article.data.name,
    fieldname: "status",
    value: "Published",
  });
}, 500);

const unpublish = debounce(() => {
  setValueRes.submit({
    doctype: "HD Article",
    name: article.data.name,
    fieldname: "status",
    value: "Draft",
  });
}, 500);

const bLabel = computed(() =>
  article.data?.status === "Published" ? "Unpublish" : "Publish"
);
const bClick = computed(() =>
  article.data?.status === "Published" ? unpublish : publish
);
const dOptions = [
  {
    label: "Edit",
    icon: IconEdit,
    onClick: () => console.log("Edit"),
  },
  {
    label: "Delete",
    icon: IconTrash,
    onClick: () => console.log("Delete"),
  },
];
</script>
