import { dayjs } from "frappe-ui";
import { computed, ref } from "vue";

/**
 * Calendar grid for a given month, as six weeks of seven days.
 *
 * Replaces frappe-ui's `useDatePicker`, dropped in 1.0.0-beta.63. Only the
 * month grid survives here — the pickers themselves are frappe-ui components.
 */
export function useDatePicker() {
  const currentYear = ref<number>(0);
  const currentMonth = ref<number>(0);

  const today = computed(() => dayjs().toDate());

  const firstOfMonth = computed(() =>
    currentYear.value && currentMonth.value
      ? dayjs(new Date(currentYear.value, currentMonth.value - 1, 1))
      : null
  );

  // Always six weeks, so the grid height never jumps between months.
  const datesAsWeeks = computed<Date[][]>(() => {
    const first = firstOfMonth.value;
    if (!first) return [];
    const start = first.subtract(first.day(), "day");
    return Array.from({ length: 6 }, (_, week) =>
      Array.from({ length: 7 }, (_, day) =>
        start.add(week * 7 + day, "day").toDate()
      )
    );
  });

  const formattedMonth = computed(() =>
    firstOfMonth.value ? firstOfMonth.value.format("MMMM, YYYY") : ""
  );

  return { currentYear, currentMonth, today, datesAsWeeks, formattedMonth };
}
