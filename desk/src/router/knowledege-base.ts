import { getPage } from "./utils";

export const KnowldegeBasePages = {
  path: "/knowledge-base",
  component: () => getPage("KBPublic"),
  children: [
    {
      path: "",
      name: "KBHome",
      component: () => getPage("KBHome"),
    },
    {
      path: ":categoryId",
      name: "KBCategoryPublic",
      component: () => getPage("KBCategoryPublic"),
      props: true,
    },
    {
      path: "articles/:articleId",
      name: "KBArticlePublic",
      component: () => getPage("KBArticlePublic"),
      meta: {
        public: true,
      },
      props: true,
    },
  ],
};
