<template>
  <div class="flex flex-col flex-1">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header> </template>
    </LayoutHeader>
    <div class="pt-6 mx-auto w-full max-w-4xl px-5">
      <div class="flex flex-col gap-3 rounded-lg border w-full p-4">
        <div class="flex justify-between items-center mb-3">
          <!-- Author Info -->
          <UserAvatar :name="user.name" :expand="true" />
          <!-- Action Buttons -->
          <div class="flex gap-2">
            <Button label="Discard" @click="handleArticleDiscard" />
            <Button
              label="Create"
              variant="solid"
              @click="handleCreateArticle"
            />
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
        />
        <!-- Article Content -->
        <TextEditor
          :content="content"
          @change="content = $event"
          placeholder="Write your article here..."
          editor-class="rounded-b-lg max-w-[unset] prose-sm h-[calc(100vh-340px)] sm:h-[calc(100vh-250px)] overflow-auto"
        >
          <template #bottom>
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
import { ref, computed } from "vue";
import {
  usePageMeta,
  TextEditor,
  TextEditorFixedMenu,
  confirmDialog,
  Breadcrumbs,
} from "frappe-ui";
import { useRouter } from "vue-router";
import { newArticle } from "@/stores/article";
import { useUserStore } from "@/stores/user";
import { LayoutHeader, UserAvatar } from "@/components";
import { createToast, textEditorMenuButtons } from "@/utils";
import { Article } from "@/types";

const userStore = useUserStore();
const user = userStore.getUser();
const router = useRouter();

const title = ref("");
const content = ref("");

function handleCreateArticle() {
  newArticle.submit(
    { title: title.value, content: content.value },
    {
      onSuccess: (article: Article) => {
        console.log(article.name);
        createToast({
          title: "Article created successfully",
          icon: "check",
          iconClasses: "text-green-600",
        });
        resetState();
        router.push({
          name: "Article",
          params: {
            articleId: article.name,
          },
        });
      },
      onError: (error: string) => {
        createToast({
          title: error,
          icon: "x",
          iconClasses: "text-red-600",
        });
      },
    }
  );
}
function handleArticleDiscard() {
  if (!title.value && !content.value) {
    return;
  }
  confirmDialog({
    title: "Discard Article",
    message: "Are you sure you want to discard this article?",
    onConfirm: ({ hideDialog }: { hideDialog: Function }) => {
      resetState();
      hideDialog();
    },
  });
}

function resetState() {
  title.value = "";
  content.value = "";
}

const breadcrumbs = computed(() => [
  {
    label: "Knowledge Base",
    route: { name: "AgentKnowledgeBase" },
  },
  {
    label: "New Article",
  },
]);

usePageMeta(() => {
  return {
    title: "New Article",
  };
});
</script>
