import { computed } from "vue";
import { userStorage } from "@/composables/userStorage";

// module-scope so every timeline component shares one reactive preference
const timestampFormat = userStorage<"Relative" | "Exact">(
  "timeline_timestamp_format",
  "Relative"
);

export function useTimelinePreferences() {
  const showExactTimestamp = computed(() => timestampFormat.value === "Exact");
  return { timestampFormat, showExactTimestamp };
}
