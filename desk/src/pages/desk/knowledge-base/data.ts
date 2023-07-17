import { ref } from "vue";
import { defineStore } from "pinia";

export const useKnowledgeBaseStore = defineStore("knowledgeBase", () => {
  const activeCategory = ref("");
  const activeSubCategory = ref("");

  return {
    activeCategory,
    activeSubCategory,
  };
});

export const icons = [
  "alert-circle",
  "atom",
  "box",
  "camera",
  "command",
  "contact-2",
  "git-branch",
  "globe",
  "headphones",
  "heart",
  "mail",
  "map",
  "messages-square",
  "music-4",
  "palmtree",
  "phone",
  "piggy-bank",
  "sparkles",
  "sprout",
  "sun",
  "trash-2",
  "trending-up",
  "truck",
  "users",
];
