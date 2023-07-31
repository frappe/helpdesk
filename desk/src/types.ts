export interface Resource<A> {
  auto: boolean;
  loading: boolean;
  data: A;
  reload: () => void;
}

export interface Comment {
  commented_by: string;
  content: string;
  is_pinned: boolean;
  name: string;
  creation: string;
}

export interface Communication {
  creation: string;
  content: string;
  name: string;
  sender: string;
  bcc?: string;
  cc?: string;
}

export interface Activity {
  action: string;
  name: string;
  owner: string;
  creation: string;
}

export interface Contact {
  full_name: string;
  name: string;
  company_name?: string;
  email_id?: string;
  image?: string;
  mobile_no?: string;
  phone?: string;
}

export interface CustomField {
  label: string;
  value: string;
  route: string;
}

export interface ViewLog {
  name: string;
  viewed_by: string;
  creation: string;
}

export interface Ticket {
  _assign: string;
  agent_group: string;
  customer: string;
  modified: string;
  name: string;
  priority: string;
  raised_by: string;
  resolution_by: string;
  response_by: string;
  status: string;
  subject: string;
  ticket_type: string;
  via_customer_portal: string;
  contact: Contact;
  comments: Comment[];
  communications: Communication[];
  history: Activity[];
  custom_fields: CustomField[];
  views: ViewLog[];
}

export interface DocField {
  fieldname: string;
  fieldtype: string;
  label: string;
  name: string;
  options: string;
}

export interface Filter {
  field: DocField;
  operator: string;
  value: boolean | number | string | string[];
}
