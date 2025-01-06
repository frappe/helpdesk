<template>
  <div>
    <LayoutHeader>
      <template #left-header>
        <div class="flex gap-1 items-center">
          <Breadcrumbs :items="breadcrumbs" />
        </div>
      </template>
      <template #right-header>
        <!-- Default Buttons -->
        <div class="flex gap-2" v-if="!editable">
          <Button
            :label="article.data?.status === 'Draft' ? 'Publish' : 'Unpublish'"
            :iconLeft="article.data?.status !== 'Published' && 'globe'"
            @click="toggleStatus()"
          />
        </div>
      </template>
    </LayoutHeader>

    <div
      class="py-4 mx-auto w-full max-w-3xl px-5 flex"
      :class="editable && 'overflow-hidden'"
      v-if="!article.loading"
    >
      <!-- article Info -->
      <div
        class="flex flex-col gap-3 p-4 w-full"
        :class="editable && 'border rounded-lg  '"
      >
        <!-- Top Element -->
        <div class="flex flex-col gap-2">
          <div class="flex gap-1 items-center justify-between">
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
                {{ dayjs(article.data.modified).short() }}
              </div>
            </div>
            <Dropdown :options="options" v-if="!editable">
              <Button variant="ghost">
                <template #icon>
                  <IconMoreHorizontal class="h-4 w-4" />
                </template>
              </Button>
            </Dropdown>
            <div class="flex gap-2" v-else>
              <DiscardButton
                :hide-dialog="!isDirty"
                title="Discard changes?"
                message="Are you sure you want to discard changes?"
                @discard="handleDiscard"
              />

              <Button label="Save" @click="handleSave" variant="solid" />
            </div>
          </div>
          <!-- Title -->
          <textarea
            ref="titleRef"
            class="w-full resize-none border-0 text-3xl font-bold placeholder-ink-gray-3 p-0 pb-3 border-b border-gray-200 focus:ring-0 focus:border-gray-200"
            v-model="title"
            placeholder="Title"
            rows="1"
            wrap="soft"
            maxlength="140"
            autofocus
            :disabled="!editable"
          />
        </div>
        <!-- Article Content -->
        <TextEditor
          ref="editorRef"
          :editor-class="editorClass"
          :content="content"
          :editable="editable"
          @change="(event:string) => {
			      content = event;
		      }"
          placeholder="Write your article here..."
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
import { computed, ref, h, watch } from "vue";
import {
  Breadcrumbs,
  debounce,
  createResource,
  Avatar,
  TextEditor,
  TextEditorFixedMenu,
  Dropdown,
  Button,
  confirmDialog,
} from "frappe-ui";
import { useRouter } from "vue-router";
import { dayjs } from "@/dayjs";
import {
  updateArticle,
  deleteRes as deleteArticle,
} from "@/stores/knowledgeBase";
import { useUserStore } from "@/stores/user";
import LayoutHeader from "@/components/LayoutHeader.vue";
import { Resource, Article } from "@/types";
import IconDot from "~icons/lucide/dot";
import { createToast, textEditorMenuButtons } from "@/utils";
import IconMoreHorizontal from "~icons/lucide/more-horizontal";
import DiscardButton from "@/components/DiscardButton.vue";

const props = defineProps({
  articleId: {
    type: String,
    required: true,
  },
});

const userStore = useUserStore();
const user = userStore.getUser();

const router = useRouter();

const editorRef = ref(null);
const editable = ref(false);
const content = ref("");
const title = ref("");

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

const article: Resource<Article> = createResource({
  url: "helpdesk.api.knowledge_base.get_article",
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
const isDirty = ref(false);

function handleEditMode() {
  editable.value = true;
  editorRef.value.editor.chain().focus("start");
}

function handleDiscard() {
  editable.value = false;
  isDirty.value = false;
  title.value = article.data.title;
  content.value = article.data.content;
}

function handleSave() {
  editable.value = false;
  handleArticleUpdate();
}

function handleArticleUpdate() {
  if (!isDirty.value) return;
  updateArticle.submit(
    {
      doctype: "HD Article",
      name: article.data.name,
      fieldname: {
        content: content.value,
        title: title.value,
      },
    },
    {
      onSuccess: () => {
        createToast({
          title: "Article updated successfully",
          icon: "check",
          iconClasses: "text-green-600",
        });
        isDirty.value = false;
        article.reload();
      },
    }
  );
}

function handleDelete() {
  confirmDialog({
    title: "Delete Article",
    message: "Are you sure you want to delete this article?",
    onConfirm: ({ hideDialog }: { hideDialog: Function }) => {
      deleteArticle.submit(
        {
          doctype: "HD Article",
          name: article.data.name,
        },
        {
          onSuccess: () => {
            createToast({
              title: "Article deleted successfully",
              icon: "check",
              iconClasses: "text-green-600",
            });
            router.push({
              name: "AgentKnowledgeBase",
            });
          },
        }
      );
      hideDialog();
    },
  });
}

watch([() => content.value, () => title.value], ([newContent, newTitle]) => {
  isDirty.value =
    newContent !== article.data.content || newTitle !== article.data.title;
});

const editorClass = computed(() => {
  let basicStyles =
    "rounded-b-lg max-w-[unset] prose-sm h-[calc(100vh-340px)] sm:h-[calc(100vh-250px)]";
  if (editable.value) {
    basicStyles += " overflow-auto";
  }
  return basicStyles;
});

const options = computed(() => [
  {
    label: "Edit",
    icon: "edit",
    onClick: () => {
      handleEditMode();
    },
  },
  {
    label: "Move To",
    icon: "corner-up-right",
    onClick: () => {},
  },
  // {
  //   label: article.data?.status === "Draft" ? "Publish" : "Unpublish",
  //   icon: article.data?.status !== "Published" ? "globe" : "x",
  //   onClick: toggleStatus,
  // },
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
        component: h(Button, {
          label: "Delete",
          variant: "ghost",
          iconLeft: "trash-2",
          theme: "red",
          style: "width: 100%; justify-content: flex-start;",
          onClick: handleDelete,
        }),
      },
    ],
  },
]);

const breadcrumbs = computed(() => {
  const items = [
    {
      label: "Knowledge Base",
      route: { name: "AgentKnowledgeBase" },
    },
  ];
  if (article.data?.category_name) {
    items.push({
      label: article.data?.category_name,
      route: { name: "AgentKnowledgeBase" },
    });
  }
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
