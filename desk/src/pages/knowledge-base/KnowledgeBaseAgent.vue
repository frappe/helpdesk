<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-9">
          {{ __("Knowledge Base") }}
        </div>
      </template>
      <template #right-header>
        <Dropdown :options="headerOptions">
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
      v-model:icon="category.icon"
      @update="handleCategoryUpdate"
      @create="handleCategoryCreate"
    />
    <MoveToCategoryModal v-model="moveToModal" @move="handleMoveToCategory" />
    <MergeCategoryModal
      :categoryTitle="category.title"
      :category-id="category.id"
      v-model="mergeModal"
      @merge="handleMergeCategory"
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
import { ArticleIcon, OrganizationsIcon } from "@/components/icons";
import LayoutHeader from "@/components/LayoutHeader.vue";
import ListViewBuilder from "@/components/ListViewBuilder.vue";
import ArticleAccessModal from "@/components/knowledge-base/ArticleAccessModal.vue";
import CategoryModal from "@/components/knowledge-base/CategoryModal.vue";
import MergeCategoryModal from "@/components/knowledge-base/MergeCategoryModal.vue";
import MoveToCategoryModal from "@/components/knowledge-base/MoveToCategoryModal.vue";
import { globalStore } from "@/stores/globalStore";
import {
  deleteArticles,
  deleteRes as deleteCategory,
  mergeCategory,
  moveToCategory,
  newCategory,
  updateCategory,
} from "@/stores/knowledgeBase";
import { capture } from "@/telemetry";
import { Error } from "@/types";
import { copyToClipboard, CUSTOMER_PORTAL_ROOT } from "@/utils";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import {
  Badge,
  Button,
  Dropdown,
  call,
  createResource,
  toast,
  usePageMeta,
} from "frappe-ui";
import { computed, h, markRaw, onMounted, reactive, ref } from "vue";
import { __ } from "@/translation";
import { useRouter } from "vue-router";
import LucideMerge from "~icons/lucide/merge";

const router = useRouter();
const { $dialog } = globalStore();

const category = reactive({
  title: "",
  id: "",
  icon: "lucide-folder",
});

const listViewRef = ref(null);
const editTitle = ref(false);

// modals state
const showCategoryModal = ref(false);
const moveToModal = ref(false);
const mergeModal = ref(false);
// One dialog for a category's articles and for a selection of them.
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
    label: __("Edit"),
    icon: "lucide-edit",
    onClick: (groupedRow) => {
      editTitle.value = true;
      showCategoryModal.value = true;
      category.title = groupedRow.group.label;
      category.id = groupedRow.group.value;
      category.icon = groupedRow.group.icon || "lucide-folder";
    },
  },
  {
    label: __("Merge"),
    icon: LucideMerge,
    onClick: (groupedRow) => {
      mergeModal.value = true;
      category.title = groupedRow.group.label;
      category.id = groupedRow.group.value;
    },
  },
  {
    label: __("Change access"),
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
        title: __("Access for “{0}”", [group.label]),
        visibility,
      });
    },
  },
  {
    label: __("Copy link"),
    icon: "lucide-link",
    onClick: ({ group }) =>
      copyToClipboard(
        window.location.origin + CUSTOMER_PORTAL_ROOT + ROUTES.category(group.value),
        __("Category link copied to clipboard.")
      ),
  },
  {
    label: __("Delete"),
    icon: "lucide-trash-2",
    onClick: (groupedRow) => {
      handleCategoryDelete(groupedRow);
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
  const name = category.title;
  if (!access) {
    return __(
      "Articles in {0} have different access. Choosing one applies it to every article.",
      [name]
    );
  }
  if (access === accessDialog.visibility) {
    return {
      Public: __(
        "Anyone, including visitors who aren't logged in, can read the articles in {0}.",
        [name]
      ),
      "Customers only": __(
        "Only logged-in customers and agents can read the articles in {0}.",
        [name]
      ),
      "Agents only": __(
        "Only agents can read the articles in {0}. It doesn't appear on the customer portal.",
        [name]
      ),
    }[access];
  }
  return {
    Public: __(
      "Every article in {0} will be readable by anyone, including visitors who aren't logged in.",
      [name]
    ),
    "Customers only": __(
      "Every article in {0} will be readable only by logged-in customers and agents.",
      [name]
    ),
    "Agents only": __(
      "Every article in {0} will be readable only by agents, and {0} will no longer appear on the customer portal.",
      [name]
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
      "Customers only": __(
        "Only logged-in customers and agents can read the selected articles."
      ),
      "Agents only": __("Only agents can read the selected articles."),
    }[access];
  }
  return {
    Public: __(
      "The selected articles will be readable by anyone, including visitors who aren't logged in."
    ),
    "Customers only": __(
      "The selected articles will be readable only by logged-in customers and agents."
    ),
    "Agents only": __("The selected articles will be readable only by agents."),
  }[access];
}

async function changeArticlesAccess(selections: Set<string>) {
  listSelections.value = new Set(selections);
  const rows = await call("frappe.client.get_list", {
    doctype: "HD Article",
    filters: { name: ["in", Array.from(selections)] },
    fields: ["visibility"],
    limit_page_length: 0,
  });
  const current = new Set(rows.map((row) => row.visibility));
  Object.assign(accessDialog, {
    open: true,
    forCategory: false,
    title:
      selections.size === 1
        ? __("Access for 1 article")
        : __("Access for {0} articles", [selections.size]),
    visibility: current.size === 1 ? [...current][0] : null,
  });
}

async function updateArticlesAccess(visibility: string) {
  const { failed_docs } = await call("frappe.client.bulk_update", {
    docs: Array.from(listSelections.value).map((docname) => ({
      doctype: "HD Article",
      docname,
      visibility,
    })),
  });
  if (failed_docs.length) {
    toast.error(__("Could not update access for some articles."));
  } else {
    toast.success(__("Access updated for the selected articles."));
  }
  listViewRef.value?.reload();
  listViewRef.value?.unselectAll();
  listSelections.value.clear();
}

const listSelections = ref(new Set());
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
    label: __("Delete"),
    icon: "lucide-trash-2",
    onClick: (selections: Set<string>) => {
      listSelections.value = selections;
      $dialog({
        title: __("Delete articles"),
        message: __("Are you sure you want to delete these articles?"),
        actions: [
          {
            label: __("Delete"),
            theme: "red",
            iconLeft: "lucide-trash-2",
            variant: "solid",
            onClick({ close }) {
              handleDeleteArticles();
              close();
            },
          },
        ],
      });
    },
  },
];

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
      icon: category.icon,
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
      fieldname: { category_name: category.title, icon: category.icon },
    },
    {
      onSuccess: () => {
        listViewRef.value.reload();
        showCategoryModal.value = false;
        editTitle.value = false;

        toast.success(__("Category updated successfully."));
        resetState();
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

function handleCategoryDelete(groupedRow) {
  $dialog({
    title: __("Delete category?"),
    message: __(
      "All articles from this category will move to General category."
    ),
    actions: [
      {
        label: __("Confirm"),
        variant: "solid",
        onClick({ close }: { close: () => void }) {
          deleteCategory.submit(
            {
              doctype: "HD Article Category",
              name: groupedRow.group.value,
            },
            {
              onSuccess: () => {
                toast.success(__("Category deleted successfully."));
                listViewRef.value.reload();
              },
            }
          );
          close();
        },
      },
    ],
  });
}

function handleDeleteArticles() {
  deleteArticles.submit(
    {
      articles: Array.from(listSelections.value),
    },
    {
      onSuccess: () => {
        listViewRef.value?.reload();
        listViewRef.value?.unselectAll();
        listSelections.value?.clear();
        toast.success(__("Articles deleted successfully."));
      },
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
  category.id = "";
  category.icon = "lucide-folder";
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
    columnConfig: {
      title: {
        prefix: () => {
          return h(ArticleIcon, {
            class: "h-4 w-4 flex-shrink-0 text-ink-gray-6",
          });
        },
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
          h("div", { class: "flex items-center gap-1.5 text-ink-gray-7" }, [
            h(Icon, {
              icon: accessIcons[item],
              class: "h-4 w-4 flex-shrink-0 text-ink-gray-6",
            }),
            __(item?.replace(" only", "")),
          ]),
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
    showSelectBanner: true,
    selectBannerActions,
    default_page_length: 100,
  };
});

const accessIcons = {
  "Agents only": "lucide-lock",
  "Customers only": OrganizationsIcon,
  Public: "lucide-globe",
};

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
