<template>
  <div>
    <LayoutHeader>
      <template #left-header>
        <div class="flex gap-2 items-center crumbs max-w-[50vw]">
          <Breadcrumbs :items="breadcrumbs" class="-ms-0.5 truncate" />
          <Badge
            v-if="!article.loading"
            variant="subtle"
            :theme="article.data?.status === 'Draft' ? 'amber' : 'green'"
            size="md"
            >{{ article.data?.status }}</Badge
          >
        </div>
      </template>
      <template #right-header>
        <!-- Default Buttons -->
        <div class="flex gap-2" v-if="!editable && !article.loading">
          <Button
            :label="isPublished ? __('Unpublish') : __('Publish')"
            :iconLeft="isPublished ? undefined : 'lucide-globe'"
            @click="togglePublished()"
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
        :class="editable && 'border rounded-6 overflow-hidden'"
      >
        <!-- Top Element -->
        <div class="flex flex-col gap-3">
          <!-- Title -->
          <div class="flex sm:flex-row flex-col justify-between">
            <div class="w-full">
              <textarea
                ref="titleRef"
                class="w-full resize-none border-0 text-3xl-bold bg-transparent placeholder-ink-gray-3 p-0 focus:ring-0 overflow-hidden"
                v-model="title"
                :placeholder="__('Title')"
                rows="1"
                wrap="soft"
                maxlength="140"
                autofocus
                :disabled="!editable"
              />
              <div
                v-if="!editable && !isMobileView"
                class="text-p-sm text-ink-gray-4 items-center"
              >
                <span>{{ views }} {{ __("views") }}</span>
              </div>
            </div>
            <div class="flex gap-4 justify-between sm:items-start">
              <div class="flex gap-4 text-p-sm items-center">
                <div class="flex items-center gap-2" v-if="!editable">
                  <Button
                    variant="ghost"
                    size="md"
                    class="flex shrink-0 !w-auto"
                    disabled
                  >
                    <template #suffix>
                      {{ likes }}
                    </template>
                    <template #icon>
                      <ThumbsUpIcon class="size-4" />
                    </template>
                  </Button>
                  <Button
                    variant="ghost"
                    size="md"
                    class="flex shrink-0 !w-auto"
                    disabled
                  >
                    <template #suffix>
                      {{ dislikes }}
                    </template>
                    <template #icon>
                      <ThumbsDownIcon class="size-4" />
                    </template>
                  </Button>
                </div>
              </div>
              <div class="flex gap-1 items-start justify-between">
                <Dropdown
                  :options="articleActions"
                  v-if="!editable"
                  @update:open="
                    (open) => open && (isConfirmingDeleteArticle = false)
                  "
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
        <Editor
          ref="editorRef"
          :model-value="textEditorContentWithIDs"
          :extensions="extensions"
          :editable="editable"
          :upload-function="
            (file: any, options: any) =>
              uploadFunction(file, 'HD Article', articleId, false, options)
          "
          @change="(event:string) => { content = event; }"
          :placeholder="__('Write your article here...')"
        >
          <template #default>
            <!-- Scroll here so selected nodes aren't clipped. -->
            <div :class="editorScrollClass">
              <EditorContent class="rounded-b-6 max-w-[unset] prose-sm" />
            </div>
            <EditorFixedMenu
              v-if="editable"
              class="-ms-1 overflow-x-auto w-full"
              :items="fullToolbar"
            />
            <EditorTableMenu v-if="editable" />
          </template>
        </Editor>
        <div v-if="!editable" class="flex gap-1 items-center pt-1.5 mt-4">
          <!-- Avatar -->
          <div class="flex gap-2 items-center justify-center">
            <Avatar
              :image="article.data.author.image"
              :label="article.data.author.name"
              size="lg"
            />
            <div class="flex flex-col justify-start gap-1">
              <p class="truncate capitalize text-p-base-medium text-ink-gray-9">
                <span class="text-base text-ink-gray-5"
                  >{{ __("published by") }}
                </span>
                {{ article.data.author.name }}
              </p>
              <div class="flex items-center gap-1">
                <span class="text-p-xs text-ink-gray-6">
                  {{
                    dayjsLocal(article.data.modified).format("MMM D, h:mm A")
                  }}
                </span>
                <IconDot v-if="isMobileView" class="h-4 w-4 text-ink-gray-5" />

                <span
                  v-if="isMobileView"
                  class="text-p-xs text-ink-gray-4 items-center"
                >
                  {{ __("{0} views", [views]) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- Loading State -->
    <div
      v-if="article.loading"
      class="w-full h-screen flex items-center justify-center"
    >
      <LoadingIndicator class="size-10" />
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
    <ArticleSharingModal
      v-if="article.data"
      v-model="showSharingModal"
      :title="article.data.title"
      :visibility="article.data.visibility"
      @publish="publishArticle"
    >
      <template #default="{ access }">
        <p
          v-if="siblingsVisibility.data && access !== siblingsVisibility.data"
          class="text-p-sm text-ink-gray-7"
        >
          {{
            __("Other articles in {0} are visible to {1}.", [
              article.data.category_name,
              visibleTo(siblingsVisibility.data),
            ])
          }}
        </p>
      </template>
    </ArticleSharingModal>
  </div>
</template>

<script setup lang="ts">
import DiscardButton from "@/components/DiscardButton.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";
import { buildEditorExtensions, fullToolbar } from "@/components/editor/config";
import { ThumbsDownIcon, ThumbsUpIcon } from "@/components/icons";
import ArticleSharingModal from "@/components/knowledge-base/ArticleSharingModal.vue";
import CategoryModal from "@/components/knowledge-base/CategoryModal.vue";
import MoveToCategoryModal from "@/components/knowledge-base/MoveToCategoryModal.vue";
import { useScreenSize } from "@/composables/screen";
import {
  deleteRes as deleteArticle,
  moveToCategory,
  newCategory,
  updateRes as updateArticle,
  useCategoryVisibility,
  visibleTo,
} from "@/stores/knowledgeBase";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { Article, Breadcrumb, Error, Resource } from "@/types";
import { ConfirmDelete, uploadFunction } from "@/utils";
import {
  Avatar,
  Badge,
  Breadcrumbs,
  Button,
  createResource,
  dayjsLocal,
  debounce,
  Dropdown,
  LoadingIndicator,
  toast,
  usePageMeta,
} from "frappe-ui";
import {
  Editor,
  EditorContent,
  EditorFixedMenu,
  EditorTableMenu,
} from "frappe-ui/editor";
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import IconDot from "~icons/lucide/dot";
import IconMoreHorizontal from "~icons/lucide/more-horizontal";

const extensions = buildEditorExtensions();
const { isMobileView } = useScreenSize();

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

const editorRef = ref(null);
const editable = ref(route.query.isEdit ?? false);
const likes = ref(0);
const dislikes = ref(0);
const views = ref(0);
const content = ref("");
const title = ref("");

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
  },
  onError: (err: Error) => {
    if (err.exc_type === "PermissionError") {
      router.replace({ name: "AgentKnowledgeBase" });
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

const isPublished = computed(() => article.data?.status === "Published");

const togglePublished = debounce(
  () =>
    isPublished.value
      ? save({ status: "Draft" }, __("Article unpublished."))
      : save({ status: "Published" }, __("Article published.")),
  300
);

const showSharingModal = ref(false);
const siblingsVisibility = useCategoryVisibility(
  computed(() => (showSharingModal.value && article.data?.category_id) || null)
);

function publishArticle(visibility: string) {
  save(
    { status: "Published", visibility },
    isPublished.value ? __("Access updated.") : __("Article published.")
  );
}

function save(values: Record<string, string>, message: string) {
  updateArticle.submit(
    { doctype: "HD Article", name: article.data.name, fieldname: values },
    {
      onSuccess: () => {
        toast.success(message);
        article.reload();
      },
    }
  );
}
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

watch(
  () => articleStats.data,
  (stats) => {
    if (stats) {
      likes.value = stats.likes;
      dislikes.value = stats.dislikes;
    }
  }
);

watch([() => content.value, () => title.value], ([newContent, newTitle]) => {
  isDirty.value =
    newContent !== article.data.content || newTitle !== article.data.title;
});

const editorScrollClass = computed(
  () =>
    editable.value &&
    "-mx-4 px-4 overflow-auto h-[calc(100vh-340px)] sm:h-[calc(100vh-250px)]"
);

const isConfirmingDeleteArticle = ref(false);

const articleActions = computed(() => [
  {
    label: __("Edit"),
    icon: "lucide-edit",
    onClick: () => {
      handleEditMode();
    },
  },

  ...(categories.data && categories.data > 1
    ? [
        {
          label: __("Move To"),
          icon: "lucide-corner-up-right",
          onClick: () => (moveToModal.value = true),
        },
      ]
    : [
        {
          label: __("Add Category"),
          icon: "lucide-folder-plus",
          onClick: () => (showCategoryModal.value = true),
        },
      ]),
  {
    label: __("Share"),
    icon: "lucide-share-2",
    onClick: () => (showSharingModal.value = true),
  },
  {
    group: __("Danger"),
    hideLabel: true,
    options: [
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
