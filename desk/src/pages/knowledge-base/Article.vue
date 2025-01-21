<template>
  <div>
    <LayoutHeader>
      <template #left-header>
        <div class="flex gap-1 items-center crumbs truncate">
          <Breadcrumbs :items="breadcrumbs" />
        </div>
      </template>
      <template #right-header v-if="!isCustomerPortal">
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
      class="py-4 mx-auto w-full max-w-3xl px-5 flex flex-col"
      v-if="!article.loading"
    >
      <!-- article Info -->
      <div
        class="flex flex-col gap-3 p-4 w-full"
        :class="editable && 'border rounded-lg overflow-hidden'"
      >
        <!-- Top Element -->
        <div class="flex flex-col gap-3">
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
                  {{ article.data.author.name }}
                </span>
              </div>
              <IconDot class="h-4 w-4 text-gray-600" />
              <div class="text-xs text-gray-500">
                {{ dayjs(article.data.modified).short() }}
              </div>
            </div>
            <Dropdown
              :options="articleActions"
              v-if="!editable && !isCustomerPortal"
            >
              <Button variant="ghost">
                <template #icon>
                  <IconMoreHorizontal class="h-4 w-4" />
                </template>
              </Button>
            </Dropdown>
            <div class="flex gap-2" v-if="editable">
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
            class="w-full resize-none border-0 text-3xl font-bold placeholder-ink-gray-3 p-0 pb-3 border-b border-gray-200 focus:ring-0 focus:border-gray-200 overflow-hidden"
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
          :content="textEditorContentWithIDs"
          :extensions="[PreserveIds]"
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
      <div class="p-4" v-if="isCustomerPortal">
        <ArticleFeedback :feedback="feedback" :article-id="articleId" />
      </div>
    </div>
    <MoveToCategoryModal v-model="moveToModal" @move="handleMoveToCategory" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, h, watch, onMounted } from "vue";
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
import { useRouter, useRoute } from "vue-router";
import { dayjs } from "@/dayjs";
import {
  updateRes as updateArticle,
  deleteRes as deleteArticle,
  moveToCategory,
  incrementView,
} from "@/stores/knowledgeBase";
import { useAuthStore } from "@/stores/auth";
import LayoutHeader from "@/components/LayoutHeader.vue";
import MoveToCategoryModal from "@/components/knowledge-base/MoveToCategoryModal.vue";
import DiscardButton from "@/components/DiscardButton.vue";
import ArticleFeedback from "@/components/knowledge-base/ArticleFeedback.vue";
import { Resource, Article, FeedbackAction, Error, Breadcrumb } from "@/types";
import {
  createToast,
  textEditorMenuButtons,
  copyToClipboard,
  isCustomerPortal,
} from "@/utils";
import { capture } from "@/telemetry";
import { PreserveIds } from "@/tiptap-extensions";
import IconMoreHorizontal from "~icons/lucide/more-horizontal";
import IconDot from "~icons/lucide/dot";
const props = defineProps({
  articleId: {
    type: String,
    required: true,
  },
});

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const editorRef = ref(null);
const editable = ref(route.query.isEdit ?? false);

const content = ref("");
const title = ref("");
const feedback = ref<FeedbackAction>();

const titleRef = ref(null);
watch(
  () => titleRef.value,
  (newVal) => {
    if (!newVal) return;

    if (newVal.scrollHeight > newVal.clientHeight) {
      newVal.style.height = newVal.scrollHeight + "px";
    }
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
    feedback.value = data.feedback;
    if (isCustomerPortal.value) {
      capture("article_viewed", {
        data: {
          user: authStore.userId,
          article: data.name,
          title: data.title,
        },
      });
      incrementArticleViews(data.name);
    }
  },
  onError: (err: Error) => {
    if (err.exc_type === "PermissionError") {
      router.replace({
        name: "CustomerKnowledgeBase",
      });
    }
  },
});

function incrementArticleViews(articleId: string) {
  incrementView.submit(
    {
      article: articleId,
    },
    {
      onError: (err: Error) => {
        if (err.exc_type === "RateLimitExceededError") {
          return;
        }
      },
    }
  );
}

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

const moveToModal = ref(false);

function handleMoveToCategory(category: string) {
  moveToCategory.submit(
    {
      category,
      articles: [props.articleId],
    },
    {
      onSuccess: () => {
        article.reload();
        moveToModal.value = false;
        createToast({
          title: "Articles moved successfully",
          icon: "check",
          iconClasses: "text-green-600",
        });
      },
      onError: (error: Error) => {
        createToast({
          title: error?.messages?.[0] || error.message,
          icon: "x",
          iconClasses: "text-red-600",
        });
        moveToModal.value = false;
      },
    }
  );
}

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
        capture("article_updated", {
          data: {
            category: props.articleId,
          },
        });
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

const textEditorContentWithIDs = computed(() =>
  article.data?.content ? addLinksToHeadings(article.data?.content) : null
);

function addLinksToHeadings(content: string) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(content, "text/html");
  const headings = doc.querySelectorAll("h2, h3, h4, h5, h6");
  headings.forEach((heading) => {
    const text = heading.textContent.trim();
    const id = text.replace(/[^a-z0-9]+/gi, "-").toLowerCase();
    heading.setAttribute("id", id);
  });
  return doc.body.innerHTML;
}
function scrollToHeading() {
  const articleHeading = window.location.hash;
  if (!articleHeading) return;
  const headingElement = document.querySelector(articleHeading) as HTMLElement;
  if (!headingElement) return;
  headingElement.scrollIntoView({ behavior: "smooth" });
  headingElement.classList.add("transition-all");
  const fontSize = headingElement.style.fontSize;
  setTimeout(() => {
    headingElement.style.fontSize = "1.5rem";
    setTimeout(() => {
      headingElement.style.fontSize = fontSize;
    }, 500);
  }, 500);
}

watch([() => content.value, () => title.value], ([newContent, newTitle]) => {
  isDirty.value =
    newContent !== article.data.content || newTitle !== article.data.title;
});

const editorClass = computed(() => {
  return [
    "rounded-b-lg max-w-[unset] prose-sm",
    editable.value &&
      "overflow-auto h-[calc(100vh-340px)] sm:h-[calc(100vh-250px)]",
  ];
});

const articleActions = computed(() => [
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
    onClick: () => (moveToModal.value = true),
  },
  {
    label: "Share",
    icon: "link",
    onClick: () => {
      const url = new URL(window.location.href);
      url.pathname = `/helpdesk/kb-public/articles/${props.articleId}`;
      copyToClipboard(url.href, article.data.title);
    },
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
  const items: Breadcrumb[] = [
    {
      label: "Knowledge Base",
      route: {
        name: isCustomerPortal.value
          ? "CustomerKnowledgeBase"
          : "AgentKnowledgeBase",
      },
    },
  ];
  if (article.data?.category_name) {
    let item = {
      label: article.data?.category_name,
    };
    if (isCustomerPortal.value) {
      item["route"] = {
        name: "Articles",
        params: {
          categoryId: article.data?.category_id,
        },
      };
    } else {
      item["route"] = {
        name: "AgentKnowledgeBase",
      };
    }
    items.push(item);
  }
  if (article.data?.title) {
    items.push({
      label: article.data?.title,
      route: { name: "Article" },
    });
  }
  return items;
});

onMounted(() => {
  setTimeout(() => {
    scrollToHeading();
  }, 100);
});
</script>
