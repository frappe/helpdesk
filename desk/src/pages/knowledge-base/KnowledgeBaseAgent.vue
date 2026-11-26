<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-9">
          {{ __("Knowledge Base") }}
        </div>
      </template>
      <template #right-header>
        <Dropdown :options="headerOptions" align="end">
          <Button
            :label="__('Create')"
            variant="solid"
            class="rtl:flex-row-reverse"
          >
            <template #prefix>
              <LucidePlus class="h-4 w-4" />
            </template>
          </Button>
        </Dropdown>
      </template>
    </LayoutHeader>
    <ListViewBuilder
      ref="listViewRef"
      :options="options"
      @row-click="(row) => $router.push(`kb/articles/${row}`)"
    />
    <CategoryModal
      :edit="editTitle"
      v-model="showCategoryModal"
      v-model:title="category.title"
      v-model:description="category.description"
      v-model:icon="category.icon"
      v-model:parent="category.parent"
      :category-id="category.id"
      @update="handleCategoryUpdate"
      @create="handleCategoryCreate"
    />
    <ArticleWeightModal
      v-model="weightModal"
      :count="listSelections.size"
      :initial-weight="selectionWeight"
      @save="handleSetWeight"
    />
    <MoveToCategoryModal
      v-model="moveToModal"
      :exclude-category="selectionCategory"
      @move="handleMoveToCategory"
    />
    <MergeCategoryModal
      :categoryTitle="category.title"
      :category-id="category.id"
      v-model="mergeModal"
      @merge="handleMergeCategory"
    />
    <DeleteCategoryModal
      v-model="deleteModal"
      :category="category.id"
      :title="category.title"
      :is-subcategory="!!category.parent"
      @confirm="handleCategoryDelete"
    />
    <ArticleAccessModal
      v-model="accessDialog.open"
      :title="accessDialog.title"
      :visibility="accessDialog.visibility"
      :action-label="__('Update access')"
      require-change
      @publish="
        accessDialog.forCategory
          ? updateCategoryAccess($event)
          : updateArticlesAccess($event)
      "
    >
      <template #default="{ access }">
        <p class="text-p-sm text-ink-gray-7">
          {{
            accessDialog.forCategory
              ? categoryAccessNote(access)
              : articlesAccessNote(access)
          }}
        </p>
      </template>
    </ArticleAccessModal>
  </div>
</template>

<script setup lang="ts">
import Icon from "@helpdesk/shared/Icon.vue";
import { MultipleAvatar } from "@/components";
import { ArticleIcon } from "@/components/icons";
import LayoutHeader from "@/components/LayoutHeader.vue";
import ListViewBuilder from "@/components/ListViewBuilder.vue";
import ArticleAccessModal from "@/components/knowledge-base/ArticleAccessModal.vue";
import ArticleWeightModal from "@/components/knowledge-base/ArticleWeightModal.vue";
import CategoryModal from "@/components/knowledge-base/CategoryModal.vue";
import DeleteCategoryModal from "@/components/knowledge-base/DeleteCategoryModal.vue";
import MergeCategoryModal from "@/components/knowledge-base/MergeCategoryModal.vue";
import MoveToCategoryModal from "@/components/knowledge-base/MoveToCategoryModal.vue";
import { globalStore } from "@/stores/globalStore";
import {
  deleteCategory,
  mergeCategory,
  moveToCategory,
  newCategory,
  updateCategory,
} from "@/stores/knowledgeBase";
import { capture } from "@/telemetry";
import { Error } from "@/types";
import { citedMessage, CUSTOMER_PORTAL_ROOT, getErrorMessage } from "@/utils";
import { copyToClipboard, countLabel } from "@helpdesk/shared/utils";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import { categoryAccess } from "@helpdesk/shared/settings/categoryAccess.ts";
import {
  Badge,
  Button,
  Dropdown,
  call,
  createResource,
  toast,
  usePageMeta,
} from "frappe-ui";
import { computed, h, markRaw, onMounted, provide, reactive, ref } from "vue";
import { __ } from "@/translation";
import { useRoute, useRouter } from "vue-router";
import LucideMerge from "~icons/lucide/merge";

const router = useRouter();
// ?category= (from an article's breadcrumb) is read once, then dropped from the URL
const route = useRoute();
const revealCategory = route.query.category as string | undefined;
if (revealCategory) {
  router.replace({ query: { ...route.query, category: undefined } });
}
const { $dialog } = globalStore();

const category = reactive({
  title: "",
  description: "",
  id: "",
  icon: "lucide-folder",
  parent: "",
  pinned: false,
});

const listViewRef = ref(null);
// Categories whose checkbox was ticked, so Delete can tell a ticked category from
// articles that happen to fill one. Lives as long as the page.
const tickedCategories = reactive(new Set<string>());
provide("tickedCategories", tickedCategories);
const editTitle = ref(false);

// modals state
const showCategoryModal = ref(false);
const moveToModal = ref(false);
const mergeModal = ref(false);
const deleteModal = ref(false);
const accessDialog = reactive({
  open: false,
  forCategory: true,
  title: "",
  visibility: null as string | null,
});
const hasActiveFilters = computed(
  () => Object.keys(listViewRef.value?.list?.params?.filters || {}).length > 0
);
const generalCategory = createResource({
  url: "helpdesk.api.knowledge_base.get_general_category",
  auto: true,
  cache: ["GeneralCategory"],
});

const headerOptions = [
  {
    label: __("Category"),
    icon: "lucide-folder",
    onClick: () => {
      resetState();
      editTitle.value = false;
      showCategoryModal.value = true;
    },
  },
  {
    label: __("Article"),
    icon: markRaw(ArticleIcon),
    onClick: () => {
      router.push({
        name: "NewArticle",
        params: {
          id: generalCategory.data,
        },
        query: {
          title: "General",
        },
      });
    },
  },
];

// General only takes articles and subcategories
const isNotGeneral = ({ group }) => group.value !== generalCategory.data;

const groupByActions = [
  {
    label: __("Add New Article"),
    icon: "lucide-plus",
    onClick: (groupedRow) => {
      router.push({
        name: "NewArticle",
        params: {
          id: groupedRow.group.value,
        },
        query: {
          title: groupedRow.group.label,
        },
      });
    },
  },
  {
    label: __("New subcategory"),
    icon: "lucide-folder-plus",
    // A Subcategory can't have its own Subcategories.
    condition: ({ group }) => !group.parent_article_category,
    onClick: ({ group }) => {
      resetState();
      category.parent = group.value;
      editTitle.value = false;
      showCategoryModal.value = true;
    },
  },
  {
    label: __("Convert to category"),
    icon: "lucide-folder-up",
    condition: ({ group }) => !!group.parent_article_category,
    onClick: async ({ group }) => {
      try {
        await call("frappe.client.set_value", {
          doctype: "HD Article Category",
          name: group.value,
          fieldname: "parent_article_category",
          value: null,
        });
      } catch (error) {
        getErrorMessage(error, true, __("Failed to update category."));
        return;
      }
      listViewRef.value.reload();
      toast.success(__("{0} is now a category", [group.category_name]));
    },
  },
  {
    label: __("Copy link"),
    condition: isNotGeneral,
    icon: "lucide-link",
    onClick: ({ group }) =>
      copyToClipboard(
        window.location.origin +
          CUSTOMER_PORTAL_ROOT +
          ROUTES.category(group.value),
        __("Category link copied to clipboard.")
      ),
  },
  {
    label: __("Edit"),
    condition: isNotGeneral,
    icon: "lucide-edit",
    onClick: ({ group }) => {
      editTitle.value = true;
      // the label is "Parent › Sub"; the plain name comes apart
      category.title = group.category_name;
      category.description = group.description || "";
      category.id = group.value;
      category.icon = group.icon || "lucide-folder";
      category.parent = group.parent_article_category || "";
      category.pinned = !!group.pinned;
      showCategoryModal.value = true;
    },
  },
  {
    label: __("Merge"),
    condition: isNotGeneral,
    icon: LucideMerge,
    onClick: (groupedRow) => {
      mergeModal.value = true;
      category.title = groupedRow.group.label;
      category.id = groupedRow.group.value;
    },
  },
  {
    label: __("Change access"),
    condition: isNotGeneral,
    icon: "lucide-lock",
    onClick: async ({ group }) => {
      category.title = group.label;
      category.id = group.value;
      const visibility = await categoryVisibility.submit({
        category: group.value,
      });
      Object.assign(accessDialog, {
        open: true,
        forCategory: true,
        title: __("Change category access"),
        visibility,
      });
    },
  },
  {
    label: __("Delete"),
    condition: isNotGeneral,
    icon: "lucide-trash-2",
    theme: "red",
    onClick: ({ group }) => {
      resetState();
      category.id = group.value;
      category.title = group.category_name;
      category.parent = group.parent_article_category || "";
      deleteModal.value = true;
    },
  },
];

const categoryVisibility = createResource({
  url: "helpdesk.api.knowledge_base.get_category_visibility",
});
const setCategoryVisibility = createResource({
  url: "helpdesk.api.knowledge_base.set_category_visibility",
});

function categoryAccessNote(access: string | null) {
  if (!access) {
    return __(
      "Articles in this category have different access. Choosing one applies it to every article."
    );
  }
  if (access === accessDialog.visibility) {
    return {
      Public: __(
        "Anyone, including visitors who aren't logged in, can read the articles in this category."
      ),
      Customers: __(
        "Only logged-in customers and agents can read the articles in this category."
      ),
      Private: __(
        "Only agents can read the articles in this category. It doesn't appear on the customer portal."
      ),
    }[access];
  }
  return {
    Public: __(
      "Every article in this category will be readable by anyone, including visitors who aren't logged in."
    ),
    Customers: __(
      "Every article in this category will be readable only by logged-in customers and agents."
    ),
    Private: __(
      "Every article in this category will be readable only by agents, and the category will no longer appear on the customer portal."
    ),
  }[access];
}

function updateCategoryAccess(visibility: string) {
  setCategoryVisibility.submit(
    { category: category.id, visibility },
    {
      onSuccess: () => {
        toast.success(
          __("Access updated for every article in {0}.", [category.title])
        );
        listViewRef.value?.reload();
      },
      onError: (error: Error) =>
        toast.error(error?.messages?.[0] || error.message),
    }
  );
}

function articlesAccessNote(access: string | null) {
  if (!access) {
    return __(
      "The selected articles have different access. Choosing one applies it to all of them."
    );
  }
  if (access === accessDialog.visibility) {
    return {
      Public: __(
        "Anyone, including visitors who aren't logged in, can read the selected articles."
      ),
      Customers: __(
        "Only logged-in customers and agents can read the selected articles."
      ),
      Private: __("Only agents can read the selected articles."),
    }[access];
  }
  return {
    Public: __(
      "The selected articles will be readable by anyone, including visitors who aren't logged in."
    ),
    Customers: __(
      "The selected articles will be readable only by logged-in customers and agents."
    ),
    Private: __("The selected articles will be readable only by agents."),
  }[access];
}

// The selected articles' value of `field`, if they all share one.
async function readSharedValue(selections: Set<string>, field: string) {
  const rows = await call("frappe.client.get_list", {
    doctype: "HD Article",
    filters: { name: ["in", Array.from(selections)] },
    fields: [field],
    limit_page_length: 0,
  });
  const values = new Set(rows.map((row) => row[field]));
  return values.size === 1 ? [...values][0] : null;
}

async function changeArticlesAccess(selections: Set<string>) {
  listSelections.value = new Set(selections);
  const visibility = await readSharedValue(selections, "visibility");
  Object.assign(accessDialog, {
    open: true,
    forCategory: false,
    title:
      selections.size === 1
        ? __("Change access for 1 article")
        : __("Change access for {0} articles", [selections.size]),
    visibility,
  });
}

function updateArticlesAccess(visibility: string) {
  return bulkUpdateArticles(
    { visibility },
    {
      failed: __("Could not update access"),
      partlyFailed: __("Could not update access for some articles."),
      saved: __("Access updated for the selected articles."),
    }
  );
}

async function bulkUpdateArticles(
  values: Record<string, unknown>,
  messages: { failed: string; partlyFailed: string; saved: string }
) {
  let failed_docs;
  try {
    ({ failed_docs } = await call("frappe.client.bulk_update", {
      docs: Array.from(listSelections.value).map((docname) => ({
        doctype: "HD Article",
        docname,
        ...values,
      })),
    }));
  } catch {
    // per-article failures come back in `failed_docs`
    toast.error(messages.failed);
    return;
  }
  if (failed_docs.length) {
    toast.error(messages.partlyFailed);
  } else {
    toast.success(messages.saved);
  }
  listViewRef.value?.reload();
  listViewRef.value?.unselectAll();
  listSelections.value.clear();
}

const listSelections = ref(new Set());
// The category every selected article is in, if they share one.
const selectionCategory = computed(() => {
  const categories = new Set(
    (listViewRef.value?.list?.data?.data || [])
      .filter((row) => listSelections.value.has(row.name))
      .map((row) => row.category)
  );
  return categories.size === 1 ? [...categories][0] : undefined;
});
const selectBannerActions = [
  {
    label: __("Change access"),
    icon: "lucide-lock",
    onClick: changeArticlesAccess,
  },
  {
    label: __("Move To"),
    icon: "lucide-corner-up-right",
    onClick: (selections: Set<string>) => {
      listSelections.value = new Set(selections);
      moveToModal.value = true;
    },
  },
  {
    label: __("Set weight"),
    icon: "lucide-arrow-up-narrow-wide",
    onClick: openWeightModal,
  },
  {
    label: __("Delete"),
    icon: "lucide-trash-2",
    onClick: deleteSelection,
  },
];

// The articles of a category and its Subcategories that the list has loaded.
function loadedBranch(value: string) {
  const data = listViewRef.value?.list?.data;
  const parentOf = new Map(
    (data?.group_by_field?.options || []).map((group) => [
      group.value,
      group.parent_article_category,
    ])
  );
  return (data?.data || [])
    .filter(
      (row) => row.category === value || parentOf.get(row.category) === value
    )
    .map((row) => row.name);
}

// Categories ticked in the list whose articles are all still selected. General
// can't be deleted, so it stays a set of articles.
function selectedCategories(selections: Set<string>) {
  const groups = (
    listViewRef.value?.list?.data?.group_by_field?.options || []
  ).filter((group) => {
    if (!tickedCategories.has(group.value)) return false;
    if (group.value === generalCategory.data) return false;
    const branch = loadedBranch(group.value);
    return branch.length && branch.every((name) => selections.has(name));
  });
  // a ticked parent already covers its Subcategories
  const values = new Set(groups.map((group) => group.value));
  return groups.filter((group) => !values.has(group.parent_article_category));
}

async function deleteSelection(selections: Set<string>) {
  listSelections.value = new Set(selections);
  const categories = selectedCategories(selections);
  const covered = new Set(
    categories.flatMap((group) => loadedBranch(group.value))
  );
  const articles = [...selections].filter((name) => !covered.has(name));
  if (categories.length === 1 && !articles.length) {
    // the row menu's dialog: keep or delete the articles, with server counts
    resetState();
    category.id = categories[0].value;
    category.title = categories[0].category_name;
    category.parent = categories[0].parent_article_category || "";
    deleteModal.value = true;
    return;
  }
  let cited: string[] = [];
  try {
    cited = await call("helpdesk.api.knowledge_base.get_cited_articles", {
      articles,
      categories: categories.map((group) => group.value),
    });
  } catch (error) {
    getErrorMessage(error, true);
    return;
  }
  // archived ones have no category, and delete is their only way out
  const archived = new Set(
    (listViewRef.value?.list?.data?.data || [])
      .filter((row) => !row.category)
      .map((row) => row.name)
  );
  const archivable = cited.filter((name) => !archived.has(name));
  const citedArchived = cited.length - archivable.length;
  const run = (archiveLinked: boolean) =>
    deleteCategoriesAndArticles(categories, articles, archiveLinked);
  $dialog({
    title:
      !categories.length && articles.every((name) => archived.has(name))
        ? countLabel(
            articles.length,
            __("Delete archived article"),
            __("Delete archived articles")
          )
        : deleteTitle(categories.length, articles.length),
    message: [
      deleteMessage(categories.length, articles.length),
      archivable.length ? citedMessage(archivable.length) : "",
      citedArchived ? citedArchivedMessage(citedArchived) : "",
    ]
      .filter(Boolean)
      .join(" "),
    actions: [
      ...(archivable.length
        ? [
            {
              label: __("Archive linked"),
              variant: "subtle",
              onClick({ close }) {
                close();
                run(true);
              },
            },
          ]
        : []),
      {
        label: __("Delete"),
        theme: "red",
        iconLeft: "lucide-trash-2",
        variant: "solid",
        onClick({ close }) {
          close();
          run(false);
        },
      },
    ],
  });
}

function deleteMessage(categories: number, articles: number) {
  if (categories) {
    return countLabel(
      categories,
      __(
        "This also deletes the category's subcategories and all its articles."
      ),
      __(
        "This also deletes the categories' subcategories and all their articles."
      )
    );
  }
  return countLabel(
    articles,
    __("Are you sure you want to delete this article?"),
    __("Are you sure you want to delete these {0} articles?")
  );
}

// Archived articles a ticket links: deleting removes them from the ticket.
function citedArchivedMessage(cited: number) {
  return countLabel(
    cited,
    __(
      "1 archived article is linked to a ticket. Deleting it removes it from the ticket."
    ),
    __(
      "{0} archived articles are linked to tickets. Deleting them removes them from those tickets."
    )
  );
}

function deleteTitle(categories: number, articles: number) {
  if (!categories) {
    return articles === 1 ? __("Delete article") : __("Delete articles");
  }
  // one category alone opens DeleteCategoryModal
  return articles
    ? __("Delete categories and articles")
    : __("Delete categories");
}

// Deletes the articles and categories; `archiveLinked` archives the ones tickets link.
async function deleteCategoriesAndArticles(
  categories: { value: string }[],
  articles: string[],
  archiveLinked: boolean
) {
  try {
    // one request, so it all happens or none of it does
    const { archived } = await call("helpdesk.api.knowledge_base.bulk_delete", {
      articles,
      categories: categories.map((group) => group.value),
      archive_linked: archiveLinked,
    });
    toast.success(
      archived
        ? countLabel(
            archived,
            __("Deleted successfully. 1 linked article was archived."),
            __("Deleted successfully. {0} linked articles were archived.")
          )
        : __("Deleted successfully.")
    );
  } catch (error) {
    getErrorMessage(error, true);
  } finally {
    listViewRef.value?.reload();
    listViewRef.value?.unselectAll();
    listSelections.value.clear();
  }
}

const weightModal = ref(false);
const selectionWeight = ref(0);

// Read, not taken from the rows: a saved list view may not fetch weight.
async function openWeightModal(selections: Set<string>) {
  listSelections.value = new Set(selections);
  // Prefilled only when the selected articles share a weight.
  selectionWeight.value = (await readSharedValue(selections, "weight")) || 0;
  weightModal.value = true;
}

function handleSetWeight(weight: number) {
  return bulkUpdateArticles(
    { weight },
    {
      failed: __("Could not update the weight"),
      partlyFailed: __("Could not update the weight for some articles."),
      saved: __("Weight updated for the selected articles."),
    }
  );
}

function handleMoveToCategory(category: string) {
  moveToCategory.submit(
    {
      category,
      articles: Array.from(listSelections.value),
    },
    {
      onSuccess: () => {
        moveToModal.value = false;
        listViewRef.value?.reload();
        listViewRef.value?.unselectAll();
        listSelections.value.clear();
        toast.success(__("Articles moved successfully."));
      },
      onError: (error: Error) => {
        const title = error?.messages?.[0] || error.message;
        toast.error(title);
        moveToModal.value = false;
      },
    }
  );
}

function handleCategoryCreate() {
  newCategory.submit(
    {
      title: category.title,
      description: category.description,
      icon: category.icon,
      parent: category.parent || null,
    },
    {
      onSuccess: (data: any) => {
        listViewRef.value.reload();
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
        toast.success(__("Category created successfully."));
        capture("category_created", {
          data: {
            category: category.title,
          },
        });
        resetState();
      },
      onError: (error: any) => {
        const message =
          error?.messages?.[0] ||
          error?.message ||
          __("Failed to create category");
        toast.error(message);
      },
    }
  );
}

function handleCategoryUpdate() {
  updateCategory.submit(
    {
      doctype: "HD Article Category",
      name: category.id,
      fieldname: {
        category_name: category.title,
        description: category.description,
        icon: category.icon,
        parent_article_category: category.parent || null,
      },
    },
    {
      onSuccess: () => {
        // nesting a pinned category unpins it
        const unpinned = category.pinned && Boolean(category.parent);
        const title = category.title;
        listViewRef.value.reload();
        showCategoryModal.value = false;
        editTitle.value = false;
        resetState();
        toast.success(
          unpinned
            ? __(
                "{0} is now a subcategory and was unpinned from the knowledge base home",
                [title]
              )
            : __("Category updated successfully.")
        );
      },
      onError: (error: any) => {
        const title =
          error?.messages?.[0] ||
          error?.message ||
          __("Failed to update category.");
        toast.error(title);
      },
    }
  );
}

async function handleCategoryDelete(
  alsoDeleteArticles: boolean,
  archiveLinked: boolean
) {
  deleteCategory.submit(
    {
      category: category.id,
      with_articles: alsoDeleteArticles,
      archive_linked: archiveLinked,
    },
    {
      onSuccess: ({ archived }) => {
        deleteModal.value = false;
        toast.success(
          archived
            ? countLabel(
                archived,
                __("Category deleted successfully. 1 article was archived."),
                __("Category deleted successfully. {0} articles were archived.")
              )
            : __("Category deleted successfully.")
        );
        listViewRef.value.reload();
        listViewRef.value.unselectAll();
        listSelections.value.clear();
        resetState();
      },
      onError: (error: Error) => getErrorMessage(error, true),
    }
  );
}

function handleMergeCategory(source: string, target: string) {
  mergeCategory.submit(
    {
      source,
      target,
    },
    {
      onSuccess: () => {
        listViewRef.value.reload();
        toast.success(__("Category merged successfully."));
        mergeModal.value = false;
        resetState();
      },
      onError: (error: Error) => {
        const title = error?.messages?.[0] || error.message;
        toast.error(title);
      },
    }
  );
}

function resetState() {
  category.title = "";
  category.description = "";
  category.id = "";
  category.icon = "lucide-folder";
  category.parent = "";
  category.pinned = false;
}

const options = computed(() => {
  return {
    doctype: "HD Article",
    selectable: true,
    view: {
      view_type: "group_by",
      group_by_field: "category",
      label_doc: "HD Article Category",
      label_field: "category_name",
      icon_field: "icon",
    },
    // the Category filter reads "Parent › Sub" from the loaded groups, not the ID
    quickFilterTitles: {
      category: (value: string) =>
        listViewRef.value?.list?.data?.group_by_field?.options?.find(
          (group) => group.value === value
        )?.label,
    },
    columnConfig: {
      title: {
        prefix: () =>
          h(ArticleIcon, { class: "size-4 shrink-0 text-ink-gray-6" }),
        custom: ({ item }) =>
          h("span", { class: "truncate text-base text-ink-gray-8" }, item),
      },
      status: {
        custom: ({ item }) => {
          return h(Badge, {
            ...statusMap[item],
          });
        },
      },
      visibility: {
        custom: ({ item }) =>
          h(
            "div",
            { class: "flex min-w-0 items-center gap-1.5 text-ink-gray-7" },
            [
              h(Icon, {
                icon: categoryAccess()[item]?.icon,
                class: "h-4 w-4 flex-shrink-0 text-ink-gray-6",
              }),
              h("span", { class: "truncate" }, categoryAccess()[item]?.label),
            ]
          ),
      },
      author: {
        custom: ({ item }) => item && h(MultipleAvatar, { avatars: [item] }),
      },
    },
    emptyState: {
      title: "No articles found",
      icon: h(ArticleIcon, {
        class: "h-10 w-10",
      }),
      description: hasActiveFilters.value
        ? __(
            "No articles found for the applied filters. Try adjusting or clearing your filters."
          )
        : __("No articles found in the following category."),
    },
    rowRoute: {
      name: "Article",
      prop: "articleId",
    },
    groupByActions,
    revealGroup: revealCategory,
    showSelectBanner: true,
    selectBannerActions,
    default_page_length: 100,
  };
});

const statusMap = {
  Published: {
    label: __("Published"),
    theme: "green",
  },
  Draft: {
    label: __("Draft"),
    theme: "amber",
  },
  Archived: {
    label: __("Archived"),
    theme: "gray",
  },
};

onMounted(() => {
  capture("kb_agent_page_viewed");
});

usePageMeta(() => {
  return {
    title: __("Knowledge Base"),
  };
});
</script>
