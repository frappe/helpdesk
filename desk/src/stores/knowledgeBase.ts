import { createResource } from "frappe-ui";

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
  makeParams({ title }) {
    return {
      title,
    };
  },
  validate({ title }) {
    if (!title) throw "Title is required";
  },
});

export const updateCategoryTitle = createResource({
  url: "frappe.client.set_value",
  validate({ name, value }) {
    if (!value) throw "Title is required";
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

export const categories = createResource({
  url: "helpdesk.api.knowledge_base.get_categories",
  cache: ["categories"],
});

export const categoryName = createResource({
  url: "helpdesk.api.knowledge_base.get_category_title",
  cache: ["categoryName"],
  makeParams({ category }) {
    return { category };
  },
});

//feedback
export const setFeedback = createResource({
  url: "run_doc_method",
  debounce: 300,
  makeParams: ({ articleId, action }) => ({
    dt: "HD Article",
    dn: articleId,
    method: "set_feedback",
    args: {
      value: action,
    },
  }),
});

// view count
export const incrementView = createResource({
  url: "helpdesk.api.knowledge_base.increment_views",
  makeParams: ({ article }) => ({
    article,
  }),
});
