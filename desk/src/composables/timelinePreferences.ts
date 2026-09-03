import { computed } from "vue";
import { userStorage } from "@/composables/userStorage";

// module-scope so every timeline component shares one reactive preference
export const timestampFormat = userStorage<"Relative" | "Exact">(
  "timeline_timestamp_format",
  "Relative"
);

export const showExactTimestamp = computed(
  () => timestampFormat.value === "Exact"
);
