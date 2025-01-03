<template>
  <div>
    <LayoutHeader>
      <template #left-header>
        <div class="flex gap-1 items-center">
          <Breadcrumbs :items="breadcrumbs" />
          <!-- <span> - </span> -->
          <Badge
            :label="article.data?.status"
            :theme="article.data?.status === 'Draft' ? 'red' : 'green'"
          />
        </div>
      </template>
      <template #right-header>
        <!-- Default Buttons -->
        <div class="flex gap-2" v-if="!editable">
          <Button label="Edit" iconLeft="edit" @click="handleEditMode" />
          <Button
            variant="solid"
            :label="article.data?.status === 'Draft' ? 'Publish' : 'Unpublish'"
            :iconLeft="article.data?.status !== 'Published' && 'globe'"
            @click="toggleStatus()"
          />
        </div>
        <!-- Edit Mode Buttons -->
        <div class="flex gap-2" v-if="editable">
          <Dropdown :options="options">
            <Button variant="ghost">
              <template #icon>
                <IconMoreHorizontal class="h-4 w-4" />
              </template>
            </Button>
          </Dropdown>
          <Button label="Save" @click="handleSave" variant="solid" />
        </div>
      </template>
    </LayoutHeader>

    <div
      class="pt-6 mx-auto w-full max-w-3xl px-5 flex"
      v-if="!article.loading"
    >
      <!-- article Info -->
      <div
        class="flex flex-col gap-8 p-4"
        :class="editable && 'border w-full rounded-lg  '"
      >
        <!-- Top Element -->
        <div class="flex gap-1 items-center">
          <!-- Avatar -->
          <div class="flex gap-1 items-center justify-center">
            <Avatar
              :image="article.data.author.image"
              :label="article.data.author.name"
            />
            <span
              class="truncate capitalize text-base text-ink-gray-9 font-medium"
            >
              {{ user.full_name || user.name }}
            </span>
          </div>
          <IconDot class="h-4 w-4 text-gray-600" />
          <div class="text-xs text-gray-500">
            {{
              dayjs(article.data.published_on || article.data.creation).short()
            }}
          </div>
        </div>
        <!-- Title -->
        <textarea
          class="w-full resize-none border-0 text-3xl font-bold placeholder-ink-gray-3 p-0 pb-3 border-b border-gray-200 focus:ring-0 focus:border-gray-200"
          v-model="title"
          placeholder="Title"
          rows="1"
          wrap="soft"
          maxlength="140"
          autofocus
          :disabled="!editable"
          v-on:change="console.log('change')"
        />
        <!-- Article Content -->
        <TextEditor
          ref="editorRef"
          :content="content"
          @change="(event:string) => {
			content = event;
			isDirty = true;
		  }"
          placeholder="Write your article here..."
          editor-class="rounded-b-lg max-w-[unset] prose-sm h-[calc(100vh-340px)] sm:h-[calc(100vh-250px)] overflow-auto"
        >
          <template #bottom v-if="editable">
            <TextEditorFixedMenu
              class="-ml-1 overflow-x-auto w-full"
              :buttons="textEditorMenuButtons"
            />
          </template>
        </TextEditor>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import {
  Breadcrumbs,
  debounce,
  createResource,
  Badge,
  Avatar,
  TextEditor,
  TextEditorFixedMenu,
  Dropdown,
  Button,
} from "frappe-ui";
import { dayjs } from "@/dayjs";
import { updateArticle } from "@/stores/article";
import { useUserStore } from "@/stores/user";
import LayoutHeader from "@/components/LayoutHeader.vue";
import { Resource, Article } from "@/types";
import IconDot from "~icons/lucide/dot";
import { createToast, textEditorMenuButtons } from "@/utils";
import IconMoreHorizontal from "~icons/lucide/more-horizontal";
import { h } from "vue";

const props = defineProps({
  articleId: {
    type: String,
    required: true,
  },
});

const userStore = useUserStore();
const user = userStore.getUser();

const editorRef = ref(null);
const editable = ref(false);
const content = ref("");
const title = ref("");

const article: Resource<Article> = createResource({
  url: "helpdesk.helpdesk.doctype.hd_article.api.get_article2",
  params: {
    name: props.articleId,
  },
  auto: true,
  onSuccess: (data: Article) => {
    content.value = data.content;
    title.value = data.title;
  },
});

const toggleStatus = debounce(() => {
  const status = article.data?.status === "Published" ? "Draft" : "Published";
  updateArticle.submit(
    {
      doctype: "HD Article",
      name: article.data.name,
      fieldname: "status",
      value: status,
    },
    {
      onSuccess: () => {
        article.reload();
      },
    }
  );
}, 300);

function handleEditMode() {
  editable.value = true;
  editorRef.value.editor.chain().focus("start");
}

function handleSave() {
  editable.value = false;
  handleArticleUpdate();
}
let isDirty: Boolean = false;
function handleArticleUpdate() {
  if (!isDirty) return;
  updateArticle.submit({
    doctype: "HD Article",
    name: article.data.name,
    fieldname: {
      content: content.value,
      title: title.value,
    },
  });
}

const options = [
  {
    label: "Move To",
    icon: "corner-up-right",
    onClick: () => {},
  },
  {
    label: "Duplicate",
    icon: "copy",
    onClick: () => {},
  },
  {
    group: "Danger",
    hideLabel: true,
    items: [
      {
        label: "Delete",
        onClick: () => {},
        component: h(Button, {
          label: "Delete",
          variant: "ghost",
          iconLeft: "trash-2",
          theme: "red",
          style: "width: 100%; justify-content: flex-start;",
        }),
      },
    ],
  },
];

const breadcrumbs = computed(() => {
  const items = [
    {
      label: "Knowledge Base",
      route: { name: "AgentKnowledgeBase" },
    },
  ];
  if (article.data?.title) {
    items.push({
      label: article.data?.title,
      route: { name: "Article" },
    });
  }
  return items;
});
</script>

<style scoped></style>
