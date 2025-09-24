export interface SlaValidationErrors {
  service_level: string;
  description: string;
  enabled: string;
  default_sla: string;
  apply_sla_for_resolution: string;
  priorities: string;
  holiday_list: string;
  default_priority: string;
  start_date: string;
  end_date: string;
  support_and_resolution: string;
  condition: string;
  [key: string]: string;
}
