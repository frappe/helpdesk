<template>
  <div>
    <LayoutHeader>
      <template #left-header>
        <div class="flex gap-2 items-center crumbs">
          <Breadcrumbs :items="breadcrumbs" class="-ml-0.5 truncate" />
          <Badge
            variant="subtle"
            :theme="article.data?.status === 'Draft' ? 'orange' : 'green'"
            size="md"
            >{{ article.data?.status }}</Badge
          >
        </div>
      </template>
      <template #right-header v-if="!isCustomerPortal">
        <!-- Default Buttons -->
        <div class="flex gap-2" v-if="!editable">
          <Button
            :label="
              article.data?.status === 'Draft' ? __('Publish') : __('Unpublish')
            "
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
                :disabled="!isDirty"
                :hide-dialog="!isDirty"
                :title="__('Discard changes?')"
                :message="__('Are you sure you want to discard changes?')"
                @discard="handleDiscard"
              />

              <Button :label="__('Save')" @click="handleSave" variant="solid" />
            </div>
          </div>
          <!-- Title -->
          <div class="flex justify-between">
            <div>
              <textarea
                ref="titleRef"
                class="w-full resize-none border-0 text-3xl font-bold placeholder-ink-gray-3 p-0 pb-1 focus:ring-0 overflow-hidden"
                v-model="title"
                :placeholder="__('Title')"
                rows="1"
                wrap="soft"
                maxlength="140"
                autofocus
                :disabled="!editable"
              />
              <div class="text-sm text-gray-500 items-center">
                <span>{{ views }} views</span>
              </div>
            </div>
            <div class="flex items-start gap-4 text-sm">
              <div class="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="md"
                  @click="handleFeedbackClick(1)"
                  class="flex"
                >
                  <template #suffix>
                    {{ likes }}
                  </template>
                  <template #icon>
                    <ThumbsUpFilledIcon v-if="feedback === 1" class="size-4" />
                    <ThumbsUpIcon v-else class="size-4" />
                  </template>
                </Button>
                <Button
                  variant="ghost"
                  size="md"
                  @click="handleFeedbackClick(2)"
                  class="flex"
                >
                  <template #suffix>
                    {{ dislikes }}
                  </template>
                  <template #icon>
                    <ThumbsDownFilledIcon
                      v-if="feedback === 2"
                      class="size-4"
                    />
                    <ThumbsDownIcon v-else class="size-4" />
                  </template>
                </Button>
              </div>
            </div>
          </div>
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
          :placeholder="__('Write your article here...')"
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
        <ArticleFeedback
          :feedback="feedback"
          :article-id="articleId"
          @article-reaction="handleFeedbackClick"
        />
      </div>
    </div>
    <MoveToCategoryModal
      v-model="moveToModal"
      @move="handleMoveToCategory"
      :exclude-category="article.data?.category_id"
    />
  </div>
</template>

<script setup lang="ts">
import DiscardButton from "@/components/DiscardButton.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";
import ArticleFeedback from "@/components/knowledge-base/ArticleFeedback.vue";
import MoveToCategoryModal from "@/components/knowledge-base/MoveToCategoryModal.vue";
import { dayjs } from "@/dayjs";
import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import {
  deleteRes as deleteArticle,
  incrementView,
  moveToCategory,
  updateRes as updateArticle,
  likeArticle,
} from "@/stores/knowledgeBase";
import { capture } from "@/telemetry";
import { PreserveIds } from "@/tiptap-extensions";
import { Article, Breadcrumb, Error, FeedbackAction, Resource } from "@/types";
import {
  copyToClipboard,
  isCustomerPortal,
  textEditorMenuButtons,
} from "@/utils";
import {
  Avatar,
  Breadcrumbs,
  Button,
  createResource,
  debounce,
  Dropdown,
  TextEditor,
  TextEditorFixedMenu,
  toast,
  Badge,
} from "frappe-ui";
import { computed, h, onMounted, ref, watch, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import IconDot from "~icons/lucide/dot";
import IconMoreHorizontal from "~icons/lucide/more-horizontal";
import { __ } from "@/translation";
import { setFeedback } from "@/stores/knowledgeBase";
import {
  ThumbsDownIcon,
  ThumbsUpIcon,
  ThumbsDownFilledIcon,
  ThumbsUpFilledIcon,
} from "@/components/icons";
const props = defineProps({
  articleId: {
    type: String,
    required: true,
  },
});

const { $dialog } = globalStore();

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const editorRef = ref(null);
const editable = ref(route.query.isEdit ?? false);
const likes = ref(0);
const dislikes = ref(0);
const views = ref(0);
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

const articleStats = createResource({
  url: "helpdesk.api.article.get_article_stats",
  params: { article_name: props.articleId },
  onSuccess(data) {
    likes.value = data.likes;
    dislikes.value = data.dislikes;
    views.value = data.views;
  },
  auto: true,
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

function handleLike() {
  likeArticle.submit(
    { article: props.articleId },
    {
      onSuccess: () => {
        if (articleStats.reload) articleStats.reload();
        toast.success(__("Thanks for your feedback."));
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
        if (status === "Published")
          toast.success("Article published successfully.");
        else toast.success("Article unpublished successfully.");
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
        toast.success(__(`Article has been successfully moved.`));
      },
      onError: (error: Error) => {
        let msg = error?.messages?.[0] || error.message;
        toast.error(msg);
        moveToModal.value = false;
      },
    }
  );
}

function handleEditMode() {
  editable.value = true;
  editorRef.value.editor.chain().focus("end").run();
}

function handleDiscard() {
  editable.value = false;
  isDirty.value = false;
  title.value = article.data.title;
  content.value = article.data.content;
  const original = addLinksToHeadings(article.data.content);
  textEditorContentWithIDs.value = null;
  nextTick(() => {
    textEditorContentWithIDs.value = original;
  });
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
        toast.success(__("Article updated"));
        isDirty.value = false;
        article.reload();
      },
    }
  );
}

function handleDelete() {
  $dialog({
    title: __("Delete Article"),
    message: __("Are you sure you want to delete this article?"),
    actions: [
      {
        label: __("Confirm"),
        variant: "solid",
        onClick({ close }) {
          deleteArticle.submit(
            {
              doctype: "HD Article",
              name: article.data.name,
            },
            {
              onSuccess: () => {
                toast.success(__("Article deleted"));
                router.push({
                  name: "AgentKnowledgeBase",
                });
              },
            }
          );
          close();
        },
      },
    ],
  });
}
const textEditorContentWithIDs = ref(null);
watch(
  () => article.data?.content,
  (newContent) => {
    if (newContent) {
      textEditorContentWithIDs.value = addLinksToHeadings(newContent);
    }
  },
  { immediate: true }
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

function handleFeedbackClick(action: FeedbackAction) {
  if (action === feedback.value) {
    action = 0;
  }
  feedback.value = action;
  setFeedback.submit(
    { articleId: props.articleId, action },
    {
      onSuccess: () => {
        if (articleStats.reload) articleStats.reload();
      },
    }
  );
}

watch(articleStats.data, () => {
  if (articleStats.data) {
    likes.value = articleStats.data.likes;
    dislikes.value = articleStats.data.dislikes;
  }
});

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
    label: __("Edit"),
    icon: "edit",
    onClick: () => {
      handleEditMode();
    },
  },
  {
    label: __("Move To"),
    icon: "corner-up-right",
    onClick: () => (moveToModal.value = true),
  },
  {
    label: __("Share"),
    icon: "link",
    onClick: () => {
      const url = new URL(window.location.href);
      url.pathname = `/helpdesk/kb-public/articles/${props.articleId}`;
      copyToClipboard(url.toString(), __("Article link copied to clipboard"));
    },
  },
  {
    group: __("Danger"),
    hideLabel: true,
    items: [
      {
        label: __("Delete"),
        component: h(Button, {
          label: __("Delete"),
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
      label: __("Knowledge Base"),
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
