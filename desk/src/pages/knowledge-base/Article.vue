<template>
  <div>
    <LayoutHeader>
      <template #left-header>
        <div class="flex gap-2 items-center crumbs">
          <Breadcrumbs :items="breadcrumbs" class="-ml-0.5 truncate" />
          <Badge
            v-if="!article.loading"
            variant="subtle"
            :theme="article.data?.status === 'Draft' ? 'orange' : 'green'"
            size="md"
            >{{ article.data?.status }}</Badge
          >
        </div>
      </template>
      <template #right-header v-if="!isCustomerPortal">
        <!-- Default Buttons -->
        <div class="flex gap-2" v-if="!editable && !article.loading">
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
          <!-- Title -->
          <div class="flex sm:flex-row flex-col justify-between">
            <div class="w-full">
              <textarea
                ref="titleRef"
                class="w-full resize-none border-0 text-3xl font-bold placeholder-ink-gray-3 p-0 focus:ring-0 overflow-hidden"
                v-model="title"
                :placeholder="__('Title')"
                rows="1"
                wrap="soft"
                maxlength="140"
                autofocus
                :disabled="!editable"
              />
              <div
                v-if="!editable && isCustomerPortal"
                class="flex gap-1 items-center pt-1.5"
              >
                <!-- Avatar -->
                <div class="flex gap-2 pb-1.5 items-center justify-center">
                  <Avatar
                    :image="article.data.author.image"
                    :label="article.data.author.name"
                    size="md"
                  />
                  <div class="flex gap-1 items-end">
                    <p class="truncate capitalize text-base text-ink-gray-7">
                      {{ article.data.author.name }}
                    </p>
                    <IconDot class="h-4 w-4 text-gray-600" />
                    <div class="text-base text-ink-gray-7">
                      {{
                        dayjsLocal(article.data.modified).format(
                          "MMM D, h:mm A"
                        )
                      }}
                    </div>
                  </div>
                </div>
              </div>
              <div
                v-if="!editable && !isCustomerPortal && !isMobileView"
                class="text-p-sm text-gray-500 items-center"
              >
                <span>{{ views }} views</span>
              </div>
            </div>
            <div class="flex gap-4 justify-between sm:items-start">
              <div class="flex gap-4 text-p-sm items-center">
                <div
                  class="flex items-center gap-2"
                  v-if="!editable && !isCustomerPortal"
                >
                  <Button
                    variant="ghost"
                    size="md"
                    class="flex shrink-0 !w-auto"
                    :disabled="!isCustomerPortal"
                  >
                    <template #suffix>
                      {{ likes }}
                    </template>
                    <template #icon>
                      <ThumbsUpFilledIcon
                        v-if="feedback === 1 && isCustomerPortal"
                        class="size-4"
                      />
                      <ThumbsUpIcon v-else class="size-4" />
                    </template>
                  </Button>
                  <Button
                    variant="ghost"
                    size="md"
                    class="flex shrink-0 !w-auto"
                    :disabled="!isCustomerPortal"
                  >
                    <template #suffix>
                      {{ dislikes }}
                    </template>
                    <template #icon>
                      <ThumbsDownFilledIcon
                        v-if="feedback === 2 && isCustomerPortal"
                        class="size-4"
                      />
                      <ThumbsDownIcon v-else class="size-4" />
                    </template>
                  </Button>
                </div>
              </div>
              <div class="flex gap-1 items-start justify-between">
                <Dropdown
                  :options="articleActions"
                  v-if="!editable && !isCustomerPortal"
                  @click="isConfirmingDeleteArticle = false"
                >
                  <Button size="md" variant="ghost">
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

                  <Button
                    :label="__('Save')"
                    @click="handleSave"
                    variant="solid"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Article Content -->
        <TextEditor
          ref="editorRef"
          :editor-class="editorClass"
          :content="textEditorContentWithIDs"
          :extensions="[ComponentUtils, CleanStyles]"
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
        <div
          v-if="!editable && !isCustomerPortal"
          class="flex gap-1 items-center pt-1.5 mt-4"
        >
          <!-- Avatar -->
          <div class="flex gap-2 items-center justify-center">
            <Avatar
              :image="article.data.author.image"
              :label="article.data.author.name"
              size="lg"
            />
            <div class="flex flex-col justify-start gap-1">
              <p
                class="truncate capitalize text-p-base text-ink-gray-9 font-medium"
              >
                <span class="text-base text-gray-600">published by </span>
                {{ article.data.author.name }}
              </p>
              <div class="flex items-center gap-1">
                <span class="text-p-xs text-gray-700">
                  {{
                    dayjsLocal(article.data.modified).format("MMM D, h:mm A")
                  }}
                </span>
                <IconDot
                  v-if="!editable && !isCustomerPortal && isMobileView"
                  class="h-4 w-4 text-gray-600"
                />

                <span
                  v-if="!editable && !isCustomerPortal && isMobileView"
                  class="text-p-xs text-gray-500 items-center"
                  >{{ views }} views</span
                >
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="p-4" v-if="isCustomerPortal">
        <ArticleFeedback :feedback="feedback" :article-id="articleId" />
      </div>
    </div>
    <!-- Loading State -->
    <div
      v-if="article.loading"
      class="w-full h-screen flex items-center justify-center"
    >
      <LoadingIndicator :scale="10" />
    </div>
    <MoveToCategoryModal
      v-model="moveToModal"
      @move="handleMoveToCategory"
      :exclude-category="article.data?.category_id"
    />
    <CategoryModal
      :edit="editTitle"
      v-model:title="category.title"
      v-model="showCategoryModal"
      @create="handleCategoryCreate"
    />
  </div>
</template>

<script setup lang="ts">
import DiscardButton from "@/components/DiscardButton.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";
import ArticleFeedback from "@/components/knowledge-base/ArticleFeedback.vue";
import CategoryModal from "@/components/knowledge-base/CategoryModal.vue";
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
import { CleanStyles, ComponentUtils } from "@/tiptap-extensions";
import { Article, Breadcrumb, Error, FeedbackAction, Resource } from "@/types";
import {
  copyToClipboard,
  isCustomerPortal,
  textEditorMenuButtons,
  ConfirmDelete,
} from "@/utils";
import { newCategory } from "@/stores/knowledgeBase";
import {
  Avatar,
  Breadcrumbs,
  Button,
  createResource,
  createListResource,
  debounce,
  Dropdown,
  TextEditor,
  TextEditorFixedMenu,
  toast,
  Badge,
  dayjsLocal,
  LoadingIndicator,
  usePageMeta,
} from "frappe-ui";
import { computed, h, onMounted, ref, watch, nextTick, reactive } from "vue";
import { useScreenSize } from "@/composables/screen";
const { isMobileView } = useScreenSize();
import { useRoute, useRouter } from "vue-router";
import IconDot from "~icons/lucide/dot";
import IconMoreHorizontal from "~icons/lucide/more-horizontal";
import { __ } from "@/translation";
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

const showCategoryModal = ref(false);
const editTitle = ref(false);

function handleCategoryCreate() {
  newCategory.submit(
    {
      title: category.title,
    },
    {
      onSuccess: (data: any) => {
        showCategoryModal.value = false;
        router.push({
          name: "Article",
          params: {
            articleId: data.article,
          },
          query: {
            category: data.category,
            title: category.title,
            isEdit: 1,
          },
        });
        //update category name in breadcrumb
        article.data.category_name = category.title;
        toast.success(__("Category created successfully."));
      },
      onError: (error: string) => {
        toast.error(error);
      },
    }
  );
}

const category = reactive({
  title: "",
  id: "",
});

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

const categories = createResource({
  url: "frappe.client.get_count",
  makeParams: () => ({
    doctype: "HD Article Category",
  }),
  auto: true,
});

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

function hasParagraphContent(html: string) {
  if (!html) return false;
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, "text/html");
  const paragraphs = doc.querySelectorAll("p");
  return Array.from(paragraphs).some((p) => {
    return p.textContent.trim().length > 0;
  });
}

function handleSave() {
  const titleVal = title.value?.trim();
  const bodyText = hasParagraphContent(content.value);

  if (!titleVal) {
    toast.error(__("Article title cannot be set as empty"));
    return;
  }

  if (!bodyText) {
    toast.error(__("Article body cannot be set as empty."));
    return;
  }

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
        toast.success(__("Article updated successfully."));
        isDirty.value = false;
        article.reload();
      },
    }
  );
}

function handleDelete() {
  deleteArticle.submit(
    { doctype: "HD Article", name: article.data.name },
    {
      onSuccess: () => {
        toast.success(__("Article deleted successfully."));
        router.push({ name: "AgentKnowledgeBase" });
      },
    }
  );
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

const isConfirmingDeleteArticle = ref(false);

const articleActions = computed(() => [
  {
    label: __("Edit"),
    icon: "edit",
    onClick: () => {
      handleEditMode();
    },
  },

  ...(categories.data && categories.data > 1
    ? [
        {
          label: __("Move To"),
          icon: "corner-up-right",
          onClick: () => (moveToModal.value = true),
        },
      ]
    : [
        {
          label: __("Add Category"),
          icon: "folder-plus",
          onClick: () => (showCategoryModal.value = true),
        },
      ]),
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
      ...ConfirmDelete({
        onConfirmDelete: handleDelete,
        isConfirmingDelete: isConfirmingDeleteArticle,
      }),
    ],
  },
]);

const breadcrumbs = computed(() => {
  const items: Breadcrumb[] = [
    {
      label: isMobileView.value ? __("KB") : __("Knowledge Base"),
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

usePageMeta(() => {
  return {
    title: article.data?.title + ` - ${article.data?.category_name} `,
  };
});
</script>
