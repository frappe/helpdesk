interface DocType {
    name: string;
    creation: string;
    modified: string;
    owner: string;
    modified_by: string;
  }

  interface ChildDocType extends DocType {
    parent?: string;
    parentfield?: string;
    parenttype?: string;
    idx?: number;
  }
  
// Last updated: 2025-08-25 12:29:02.646874
export interface HDTicketStatus extends DocType {
  /** Color: Select */
  color?:
    | "Black"
    | "Gray"
    | "Blue"
    | "Green"
    | "Red"
    | "Pink"
    | "Orange"
    | "Amber"
    | "Yellow"
    | "Cyan"
    | "Teal"
    | "Violet"
    | "purple";
  /** Label: Data */
  label_agent: string;
  /** Show end users a different view: Check */
  different_view: 0 | 1;
  /** Label (customer view): Data */
  label_customer?: string;
  /** Category: Select */
  category: "Open" | "Paused" | "Resolved";
  /** Order: Int */
  order?: number;
  /** Enabled: Check */
  enabled: 0 | 1;
  parsed_color?: string;
}

// Last updated: 2026-01-20 15:18:57.195606
export interface HDTicket extends DocType {
  /** Subject: Data */
  subject: string;
  /** Raised By (Email): Data */
  raised_by?: string;
  /** Status: Link (HD Ticket Status) */
  status?: string;
  /** Priority: Link (HD Ticket Priority) */
  priority?: string;
  /** Ticket Type: Link (HD Ticket Type) */
  ticket_type?: string;
  /** Team: Link (HD Team) */
  agent_group?: string;
  /** Ticket Split From: Link (HD Ticket) */
  ticket_split_from?: string;
  /** Description: Text Editor */
  description?: string;
  /** Template: Link (HD Ticket Template) */
  template?: string;
  /** SLA: Link (HD Service Level Agreement) */
  sla?: string;
  /** Response By: Datetime */
  response_by?: string;
  /** SLA Status: Select */
  agreement_status?: '' | 'First Response Due' | 'Resolution Due' | 'Failed' | 'Fulfilled' | 'Paused';
  /** Resolution By: Datetime */
  resolution_by?: string;
  /** SLA Creation: Datetime */
  service_level_agreement_creation?: string;
  /** On Hold Since: Datetime */
  on_hold_since?: string;
  /** Total Hold Time: Duration */
  total_hold_time?: any;
  /** First Response Time: Duration */
  first_response_time?: any;
  /** First Responded On: Datetime */
  first_responded_on?: string;
  /** Average Response Time: Duration */
  avg_response_time?: any;
  /** Resolution Details: Text Editor */
  resolution_details?: string;
  /** Opening Date: Date */
  opening_date?: string;
  /** Opening Time: Time */
  opening_time?: any;
  /** Resolution Date: Datetime */
  resolution_date?: string;
  /** Resolution Time: Duration */
  resolution_time?: any;
  /** User Resolution Time: Duration */
  user_resolution_time?: any;
  /** Contact: Link (Contact) */
  contact?: string;
  /** Customer: Link (HD Customer) */
  customer?: string;
  /** Email Account: Link (Email Account) */
  email_account?: string;
  /** Via Customer Portal: Check */
  via_customer_portal: 0 | 1;
  /** Attachment: Attach */
  attachment?: any;
  /** Content Type: Data */
  content_type?: string;
  /** Feedback (Extra): Long Text */
  feedback_extra?: any;
  /** Feedback (Option): Link (HD Ticket Feedback Option) */
  feedback?: string;
  /** Rating: Rating */
  feedback_rating?: any;
  /** Summary: Text Editor */
  summary?: string;
  /** Ticket Merged: Check */
  is_merged: 0 | 1;
  /** Merged With: Link (HD Ticket) */
  merged_with?: string;
  /** Key: Data */
  key?: string;
  /** Status Category: Data */
  status_category?: string;
  /** Ticket raised outside working hours: Check */
  raised_outside_working_hours: 0 | 1;
}

// Last updated: 2024-03-23 16:01:27.847608
export interface AssignmentRuleUser extends ChildDocType {
  /** User: Link (User) */
  user: string;
}

// Last updated: 2024-03-23 16:01:27.759155
export interface AssignmentRuleDay extends ChildDocType {
  /** Day: Select */
  day?: 'Monday' | 'Tuesday' | 'Wednesday' | 'Thursday' | 'Friday' | 'Saturday' | 'Sunday';
}

// Last updated: 2025-08-25 17:09:11.644603
export interface AssignmentRule extends DocType {
  /** Document Type: Link (DocType) */
  document_type: string;
  /** Priority: Int */
  priority?: number;
  /** Disabled: Check */
  disabled: 0 | 1;
  /** Description: Small Text */
  description: string;
  /** Assign Condition: Code */
  assign_condition: string;
  /** Unassign Condition: Code */
  unassign_condition?: string;
  /** Rule: Select */
  rule: 'Round Robin' | 'Load Balancing' | 'Based on Field';
  /** Users: Table MultiSelect (Assignment Rule User) */
  users: AssignmentRuleUser[];
  /** Last User: Link (User) */
  last_user?: string;
  /** Close Condition: Code */
  close_condition?: string;
  /** Assignment Days: Table (Assignment Rule Day) */
  assignment_days: AssignmentRuleDay[];
  /** Due Date Based On: Select */
  due_date_based_on?: any;
  /** Field: Select */
  field?: any;
}

// Last updated: 2021-12-23 19:03:23.507845
export interface HDHoliday extends ChildDocType {
  /** Date: Date */
  holiday_date: string;
  /** Description: Text Editor */
  description: string;
  /** Weekly Off: Check */
  weekly_off: 0 | 1;
}

// Last updated: 2026-02-02 12:46:20.573677
export interface HDServiceHolidayList extends DocType {
  /** Holiday List Name: Data */
  holiday_list_name: string;
  /** From Date: Date */
  from_date: string;
  /** To Date: Date */
  to_date: string;
  /** Total Holidays: Int */
  total_holidays?: number;
  /** Weekly Off: Select */
  weekly_off?: '' | 'Sunday' | 'Monday' | 'Tuesday' | 'Wednesday' | 'Thursday' | 'Friday' | 'Saturday';
  /** Holidays: Table (HD Holiday) */
  holidays: HDHoliday[];
  /** Color: Color */
  color?: string;
  /** Description: Data */
  description?: string;
  /** Recurring holidays: JSON */
  recurring_holidays?: any;
}

// Last updated: 2021-10-21 14:27:08.190239
export interface HDServiceDay extends ChildDocType {
  /** Workday: Select */
  workday: 'Monday' | 'Tuesday' | 'Wednesday' | 'Thursday' | 'Friday' | 'Saturday' | 'Sunday';
  /** Start Time: Time */
  start_time: any;
  /** End Time: Time */
  end_time: any;
}

// Last updated: 2023-03-26 22:41:29.978960
export interface HDServiceLevelPriority extends ChildDocType {
  /** Priority: Link (HD Ticket Priority) */
  priority: string;
  /** Resolution Time: Duration */
  resolution_time?: any;
  /** Default Priority: Check */
  default_priority: 0 | 1;
  /** First Response Time: Duration */
  response_time: any;
}

// Last updated: 2026-02-02 11:54:59.519053
export interface HDServiceLevelAgreement extends DocType {
  /** Service Level Name: Data */
  service_level: string;
  /** Holiday List: Link (HD Service Holiday List) */
  holiday_list: string;
  /** Start Date: Date */
  start_date?: string;
  /** End Date: Date */
  end_date?: string;
  /** Working Hours: Table (HD Service Day) */
  support_and_resolution: HDServiceDay[];
  /** Priorities: Table (HD Service Level Priority) */
  priorities: HDServiceLevelPriority[];
  /** Default SLA: Check */
  default_sla: 0 | 1;
  /** Default Priority: Link (HD Ticket Priority) */
  default_priority?: string;
  /** Enabled: Check */
  enabled: 0 | 1;
  /** Apply SLA for Resolution Time: Check */
  apply_sla_for_resolution: 0 | 1;
  /** Condition: Code */
  condition?: string;
  /** Description: Data */
  description?: string;
  /** Condition: Code */
  condition_json?: string;
  /** Ticket Reopen status: Link (HD Ticket Status) */
  ticket_reopen_status?: string;
  /** Default Ticket Status: Link (HD Ticket Status) */
  default_ticket_status?: string;
}

// Last updated: 2026-01-19 23:22:29.075052
export interface HDAgent extends DocType {
  /** User: Link (User) */
  user: string;
  /** Agent Name: Data */
  agent_name: string;
  /** Is Active: Check */
  is_active: 0 | 1;
  /** Image: Attach Image */
  user_image?: string;
}
