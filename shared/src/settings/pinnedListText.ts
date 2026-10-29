import { __ } from "../translation";
import type { PinKind } from "./knowledgeBaseDraft";

// A function so labels translate once loaded.
export function pinnedListText(kind: PinKind) {
  return {
    categories: {
      title: __("Pinned categories"),
      customize: __("Customize pinned categories"),
      description: __(
        "Pinned categories will appear first on your knowledge base home page, in this order."
      ),
      empty: __(
        "Nothing pinned yet. The home page will list all categories alphabetically."
      ),
      search: __("Search categories to pin"),
      others: __("Other categories"),
      allPinned: __("Every category is pinned"),
      none: __("No categories found"),
      defaultIcon: "lucide-folder",
    },
    articles: {
      title: __("Pinned articles"),
      customize: __("Customize pinned articles"),
      description: __(
        "Pinned articles will appear as featured articles on your knowledge base home page, in this order."
      ),
      empty: __("Nothing pinned yet. The home page will show no featured articles."),
      search: __("Search articles to pin"),
      others: __("Other articles"),
      allPinned: __("Every article is pinned"),
      none: __("No published articles found"),
      defaultIcon: "lucide-file-text",
    },
  }[kind];
}
