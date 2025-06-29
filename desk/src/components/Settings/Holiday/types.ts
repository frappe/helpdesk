export interface Holiday {
  description: string;
  holiday_date: string | Date;
  weekly_off?: number;
  idx?: number;
  [key: string]: any;
}

export interface RepetitionPattern {
  all: boolean;
  first: boolean;
  second: boolean;
  third: boolean;
  fourth: boolean;
  fifth: boolean;
  [key: string]: boolean;
}

export interface HolidayErrors {
  holiday_list_name?: string;
  from_date?: string;
  end_date?: string;
  dateRange?: string;
  holidays?: string;
}
