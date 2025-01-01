<template>
  <div class="flex flex-col flex-1">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900 truncate">
          Knowledge base / {{ title || "New article" }}
        </div>
      </template>
      <template #right-header> </template>
    </LayoutHeader>
    <div class="pt-6 mx-auto w-full max-w-4xl px-5">
      <div class="flex flex-col gap-3 rounded-lg border w-full p-4">
        <div class="flex justify-between items-center mb-3">
          <!-- Author Info -->
          <div class="flex gap-1 items-center">
            <Avatar :image="user.user_image" :label="user.full_name" />
            <span
              class="truncate capitalize text-base text-ink-gray-9 font-medium"
            >
              {{ user.full_name || user.name }}
            </span>
          </div>
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
        <!-- Article Content  -->
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
import { ref } from "vue";
import {
  usePageMeta,
  TextEditor,
  Avatar,
  TextEditorFixedMenu,
  confirmDialog,
} from "frappe-ui";
import { useUserStore } from "@/stores/user";
import { newArticle } from "@/stores/article";
import LayoutHeader from "@/components/LayoutHeader.vue";
import { createToast, textEditorMenuButtons } from "@/utils";
import { useRouter } from "vue-router";

const userStore = useUserStore();
const user = userStore.getUser();
const router = useRouter();

const title = ref("");
const content = ref("");

function handleCreateArticle() {
  newArticle.submit(
    { title: title.value, content: content.value },
    {
      onSuccess: (article: Object) => {
        console.log(article.name);
        createToast({
          title: "Article created successfully",
          icon: "check",
          iconClasses: "text-green-600",
        });
        resetState();
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

usePageMeta(() => {
  return {
    title: "New Article",
  };
});
</script>
