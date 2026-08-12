import { computed, ref } from "vue";
import { defineStore } from "pinia";

export const useTicketPriorityStore = defineStore("ticketPriority", () => {
  const options = ref(["Urgent", "High", "Medium", "Low", "Unclassified"]);

  const colorMap: Record<string, string> = {
    Urgent: "red",
    High: "orange",
    Medium: "blue",
    Low: "green",
    Unclassified: "gray",
  };

  const badgeThemeMap: Record<string, string> = {
    Urgent: "red",
    High: "orange",
    Medium: "blue",
    Low: "green",
    Unclassified: "gray",
  };

  const textColorMap: Record<string, string> = {
    Urgent: "!text-red-600",
    High: "!text-orange-600",
    Medium: "!text-blue-600",
    Low: "!text-green-600",
    Unclassified: "!text-gray-600",
  };

  const badgeClasses: Record<string, string> = {
    Urgent: "bg-red-50 text-red-700 border border-red-200 font-medium px-2 py-0.5 rounded-full text-xs inline-flex items-center gap-1.5",
    High: "bg-orange-50 text-orange-700 border border-orange-200 font-medium px-2 py-0.5 rounded-full text-xs inline-flex items-center gap-1.5",
    Medium: "bg-blue-50 text-blue-700 border border-blue-200 font-medium px-2 py-0.5 rounded-full text-xs inline-flex items-center gap-1.5",
    Low: "bg-green-50 text-green-700 border border-green-200 font-medium px-2 py-0.5 rounded-full text-xs inline-flex items-center gap-1.5",
    Unclassified: "bg-gray-50 text-gray-700 border border-gray-200 font-medium px-2 py-0.5 rounded-full text-xs inline-flex items-center gap-1.5",
  };

  const dotColorMap: Record<string, string> = {
    Urgent: "bg-red-500",
    High: "bg-orange-500",
    Medium: "bg-blue-500",
    Low: "bg-green-500",
    Unclassified: "bg-gray-400",
  };

  function getBadgeTheme(priority: string): string {
    return badgeThemeMap[priority] || "gray";
  }

  function getBadgeClass(priority: string): string {
    return badgeClasses[priority] || badgeClasses.Unclassified;
  }

  function getDotClass(priority: string): string {
    return dotColorMap[priority] || dotColorMap.Unclassified;
  }

  return {
    options,
    colorMap,
    badgeThemeMap,
    textColorMap,
    badgeClasses,
    dotColorMap,
    getBadgeTheme,
    getBadgeClass,
    getDotClass,
  };
});
