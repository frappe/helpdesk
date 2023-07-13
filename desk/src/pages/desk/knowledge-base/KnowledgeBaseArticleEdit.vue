<template>
  <div class="flex flex-col">
    <TopBar
      :back-to="{ name: AGENT_PORTAL_KNOWLEDGE_BASE }"
      :title="article.data?.title"
      class="sticky top-0"
    >
      <template #right>
        <div class="flex gap-2">
          <Button label="Cancel" theme="gray" variant="subtle" />
          <Button
            label="Save"
            theme="gray"
            variant="solid"
            @click="setValueRes.submit"
          />
        </div>
      </template>
    </TopBar>
    <div
      class="my-6 grow place-self-center rounded-xl"
      :style="{
        width: '790px',
        'box-shadow':
          '0px 1px 2px 0px rgba(0, 0, 0, 0.1), 0px 0px 1px 0px rgba(0, 0, 0, 0.45)',
      }"
    >
      <TextEditor
        :bubble-menu="true"
        :content="article.data?.content"
        :floating-menu="true"
        class="rounded-xl px-6 py-4"
        editor-class="prose prose-sm max-w-none my-4"
        placeholder="Write something..."
        @change="article.data.content = $event"
      >
        <template #top>
          <div
            class="mb-7 flex w-max items-center gap-1 rounded bg-gray-100 px-2 py-1"
          >
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
            </div>
            <div class="flex items-center gap-2 text-sm text-gray-600">
              <div class="text-gray-600">Created</div>
              <div class="text-gray-800">
                {{ created }}
              </div>
              <div class="text-base text-gray-300">|</div>
              <div class="text-gray-600">Modified</div>
              <div class="text-gray-800">
                {{ modified }}
              </div>
              <div class="text-base text-gray-300">|</div>
              <IconThumbsUp class="h-4 w-4" />
              <div class="text-gray-600">Likes</div>
              <div class="text-gray-800">
                {{ article.data?.helpful }}
              </div>
              <div class="text-base text-gray-300">|</div>
              <IconThumbsDown class="h-4 w-4" />
              <div class="text-gray-600">Dislikes</div>
              <div class="text-gray-800">
                {{ article.data?.not_helpful }}
              </div>
            </div>
          </div>
          <div class="border-b pb-3 text-3xl font-semibold text-gray-900">
            {{ article.data?.title }}
          </div>
        </template>
      </TextEditor>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from "vue";
import { createResource, Avatar, Button, TextEditor } from "frappe-ui";
import dayjs from "dayjs";
import { AGENT_PORTAL_KNOWLEDGE_BASE } from "@/router";
import { useKeymapStore } from "@/stores/keymap";
import { createToast } from "@/utils/toasts";
import TopBar from "@/components/TopBar.vue";
import IconChevronRight from "~icons/lucide/chevron-right";
import IconThumbsDown from "~icons/lucide/thumbs-down";
import IconThumbsUp from "~icons/lucide/thumbs-up";

const article = createResource({
  url: "helpdesk.helpdesk.doctype.hd_article.api.get_article",
  params: {
    name: "de99e3d725",
  },
  auto: true,
});

const setValueRes = createResource({
  url: "frappe.client.set_value",
  debounce: 500,
  makeParams() {
    return {
      doctype: "HD Article",
      name: article.data.name,
      fieldname: "content",
      value: article.data.content,
    };
  },
  onSuccess() {
    article.reload();
    createToast({
      title: "Article updated",
      icon: "check",
      iconClasses: "text-green-500",
    });
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

const created = computed(() => dayjs(article.data?.creation).fromNow());
const modified = computed(() => dayjs(article.data?.modified).fromNow());

const keymapStore = useKeymapStore();
const keycomboSave = ["Control", "S"];
onMounted(() =>
  keymapStore.add(keycomboSave, setValueRes.submit, "Save article")
);
onBeforeUnmount(() => keymapStore.remove(keycomboSave));
</script>
