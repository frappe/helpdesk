import { createResource } from "frappe-ui";
import { type Ref, watch } from "vue";
import { __ } from "@/translation";

// Title
export const newArticle = createResource({
  url: "frappe.client.insert",
  makeParams({ title, content, category }) {
    return {
      doc: {
        doctype: "HD Article",
        title,
        content,
        category,
      },
    };
  },
  validate({ doc }) {
    if (!doc.title) throw "Title is required";
    if (!doc.content) throw "Content is required";
  },
});

export const updateRes = createResource({
  url: "frappe.client.set_value",
});

export const deleteRes = createResource({
  url: "frappe.client.delete",
});

export const deleteArticles = createResource({
  url: "helpdesk.api.knowledge_base.delete_articles",
  makeParams({ articles }) {
    return {
      articles,
    };
  },
  validate({ articles }) {
    if (!articles) throw "Articles are required";
  },
});

// Category
export const newCategory = createResource({
  url: "helpdesk.api.knowledge_base.create_category",
  makeParams({ title, icon }) {
    return {
      title,
      icon,
    };
  },
  validate({ title }) {
    if (!title) throw "Title is required";
  },
});

export const updateCategory = createResource({
  url: "frappe.client.set_value",
  validate({ fieldname }) {
    if (!fieldname.category_name) throw "Title is required";
  },
});

export const moveToCategory = createResource({
  url: "helpdesk.api.knowledge_base.move_to_category",
  makeParams({ category, articles }) {
    return {
      category,
      articles,
    };
  },
  validate({ category, articles }) {
    if (!category) throw { message: "Category is required" };
    if (!articles) throw { message: "Articles are required" };
  },
});

export const mergeCategory = createResource({
  url: "helpdesk.api.knowledge_base.merge_category",
  makeParams({ source, target }) {
    return {
      source,
      target,
    };
  },
  validate({ source, target }) {
    if (!source) throw { message: "Category is required" };
    if (!target) throw { message: "Target is required" };
  },
});

// The access every article in a category shares; `data` is null when they differ.
export function useCategoryVisibility(
  category: Ref<string | null | undefined>
) {
  const visibility = createResource({
    url: "helpdesk.api.knowledge_base.get_category_visibility",
  });
  watch(
    category,
    (name) =>
      name ? visibility.submit({ category: name }) : visibility.reset(),
    { immediate: true }
  );
  return visibility;
}

export function visibleTo(visibility: string) {
  return {
    Public: __("everyone"),
    "Customers only": __("customers only"),
    "Agents only": __("agents only"),
  }[visibility];
}
