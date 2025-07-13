import {
  Holiday,
  HolidayErrors,
  RepetitionPattern,
} from "@/components/Settings/Holiday/types";
import dayjs, { Dayjs } from "dayjs";
import { ref } from "vue";

export const holidayListActiveScreen = ref<{
  screen: "list" | "view";
  data: Record<string, any> | null;
  previousScreen?: {
    screen: "list" | "view";
    data: string;
  };
}>({ screen: "list", data: null });

export const holidayDataErrors = ref<HolidayErrors>({
  holiday_list_name: "",
  from_date: "",
  to_date: "",
});

export const holidayData = ref({
  holiday_list_name: "",
  description: "",
  associate_holiday_list: true,
  loading: false,
  total_holidays: 0,
  holidays: [],
  from_date: null,
  to_date: null,
  recurring_holidays: [],
});

export const resetHolidayData = () => {
  holidayData.value = {
    holiday_list_name: "",
    description: "",
    associate_holiday_list: true,
    loading: false,
    total_holidays: 0,
    holidays: [],
    from_date: null,
    to_date: null,
    recurring_holidays: [],
  };
};

type HolidayField = keyof HolidayErrors;

export const validateHoliday = (key?: HolidayField) => {
  const validateField = (field: HolidayField) => {
    if (key && field !== key) return;

    switch (field) {
      case "holiday_list_name":
        if (!holidayData.value.holiday_list_name?.trim()) {
          holidayDataErrors.value.holiday_list_name =
            "Holiday list name is required";
        } else {
          holidayDataErrors.value.holiday_list_name = "";
        }
        break;
      case "from_date":
        if (!holidayData.value.from_date) {
          holidayDataErrors.value.from_date = "Start date is required";
        } else {
          holidayDataErrors.value.from_date = "";
        }

        if (holidayData.value.to_date) {
          const startDate = new Date(holidayData.value.from_date);
          const endDate = new Date(holidayData.value.to_date);

          if (startDate > endDate) {
            holidayDataErrors.value.dateRange =
              "Start date cannot be after end date";
          } else {
            holidayDataErrors.value.dateRange = "";
          }
        }
        break;
      case "to_date":
        if (!holidayData.value.to_date) {
          holidayDataErrors.value.to_date = "End date is required";
        } else {
          holidayDataErrors.value.to_date = "";
        }

        if (holidayData.value.from_date) {
          const startDate = new Date(holidayData.value.from_date);
          const endDate = new Date(holidayData.value.to_date);

          if (startDate > endDate) {
            holidayDataErrors.value.dateRange =
              "Start date cannot be after end date";
          } else {
            holidayDataErrors.value.dateRange = "";
          }
        }
        break;
      default:
        break;
    }
  };

  if (key) {
    validateField(key);
  } else {
    (Object.keys(holidayDataErrors.value) as HolidayField[]).forEach(
      validateField
    );
  }

  return holidayDataErrors.value;
};

export function updateWeeklyOffDates() {
  const newHolidays = holidayData.value.holidays.filter((h) => !h.weekly_off);

  for (const day of holidayData.value.recurring_holidays) {
    const weeklyOffs = getWeeklyOffDates(
      holidayData.value.from_date,
      holidayData.value.to_date,
      day.day,
      newHolidays,
      day.repetition
    );
    newHolidays.push(...weeklyOffs);
  }
  holidayData.value.holidays = newHolidays;
}

function getWeekOfMonth(date: Dayjs): number {
  const firstDayOfMonth = date.startOf("month");
  const firstDayOfWeek = firstDayOfMonth.day();
  const offset = (date.date() + firstDayOfWeek - 1) / 7;
  return Math.ceil(offset);
}

function getWeeklyOffDateList(
  startDate: string | Date,
  endDate: string | Date,
  weeklyOff: string,
  holidays: Holiday[] = [],
  repetition?: RepetitionPattern
): Date[] {
  const start = dayjs(startDate);
  const end = dayjs(endDate);
  const dateList: Date[] = [];

  const dayMap: Record<string, number> = {
    sunday: 0,
    monday: 1,
    tuesday: 2,
    wednesday: 3,
    thursday: 4,
    friday: 5,
    saturday: 6,
  };

  const targetDay = dayMap[weeklyOff.toLowerCase()];
  if (targetDay === undefined) {
    return dateList;
  }

  const existingDates = holidays.map((h) =>
    dayjs(h.holiday_date).startOf("day").toDate()
  );

  let currentDate = start.day(targetDay);
  if (currentDate.isBefore(start, "day")) {
    currentDate = currentDate.add(1, "week");
  }
  const useAllOccurrences = !repetition || repetition.all;

  while (currentDate.isSameOrBefore(end, "day")) {
    const currentDateObj = currentDate.toDate();
    const currentDateStart = dayjs(currentDateObj).startOf("day");

    if (useAllOccurrences || shouldIncludeDate(currentDate, repetition)) {
      if (
        !existingDates.some((d) =>
          dayjs(d).startOf("day").isSame(currentDateStart)
        )
      ) {
        dateList.push(currentDateObj);
      }
    }
    currentDate = currentDate.add(1, "week");
  }

  return dateList;
}

function shouldIncludeDate(
  date: Dayjs,
  repetition: RepetitionPattern
): boolean {
  if (repetition.all) return true;

  const weekOfMonth = getWeekOfMonth(date);

  switch (weekOfMonth) {
    case 1:
      return repetition.first;
    case 2:
      return repetition.second;
    case 3:
      return repetition.third;
    case 4:
      return repetition.fourth;
    case 5:
      return repetition.fifth;
    default:
      return false;
  }
}

function getWeeklyOffDates(
  startDate: string | Date,
  endDate: string | Date,
  weeklyOff: string,
  holidays: Holiday[] = [],
  repetition: RepetitionPattern = {
    all: true,
    first: false,
    second: false,
    third: false,
    fourth: false,
    fifth: false,
  }
): Holiday[] {
  const dateList = getWeeklyOffDateList(
    startDate,
    endDate,
    weeklyOff,
    holidays,
    repetition
  );
  return dateList.map((date, index) => ({
    description: weeklyOff.charAt(0).toUpperCase() + weeklyOff.slice(1),
    holiday_date: date,
    weekly_off: 1,
    idx: index + 1,
    repetition: repetition,
  }));
}
