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

// Last updated: 2025-09-04 19:44:36.006061
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
}
