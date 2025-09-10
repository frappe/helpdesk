import { Dayjs } from "dayjs";
import { Component, ComputedRef, InjectionKey } from "vue";
import type { HDTicket } from "./types/doctypes";

export interface Resource<T = unknown> {
  auto: boolean;
  loading: boolean;
  data: T;
  pageLength: number;
  totalCount: number;
  hasNextPage: boolean;
  promise: Promise<void> | null;
  list: {
    loading: boolean;
  };
  next: () => void;
  reload: () => void;
  update: (r: unknown) => void;
}

export interface Error {
  exc_type: string;
  exc: string;
  response: string;
  status: string;
  messages: string;
  stack: string;
  message: string;
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
  fieldname: string;
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
  assignee: UserInfo;
  agent_group: string;
  customer: string;
  modified: string;
  name: string;
  priority: string;
  raised_by: string;
  resolution_by: string;
  response_by: string;
  first_responded_on: string;
  resolution_date: string;
  resolution_time: number;
  status: string;
  subject: string;
  ticket_type: string;
  via_customer_portal: string;
  agreement_status: string;
  creation: string;
  feedback_rating?: number;
  feedback_extra?: string;
  contact: Contact;
  comments: Comment[];
  communications: Communication[];
  history: Activity[];
  template: Template;
  views: ViewLog[];
  _customActions: Function[];
  is_merged?: boolean;
  status_category: "Open" | "Paused" | "Resolved";
}

export interface DocField {
  fieldname: string;
  fieldtype: string;
  label: string;
  name: string;
  options: string;
}

export interface Filter {
  field?: DocField;
  fieldname: string;
  operator: string;
  label: string;
  value: boolean | number | string;
}

export interface AutoCompleteItem {
  label: string;
  value: string;
}

export interface Field {
  fieldname: string;
  fieldtype: string;
  hide_from_customer?: 0 | 1;
  label: string;
  options: string;
  required: 0 | 1;
  description?: null;
  url_method?: string;
  link_filters?: string;
  filters?: string;
  display_via_depends_on?: string;
  mandatory_via_depends_on?: string;
  disabled?: boolean;
  placeholder?: string | null;
  readonly?: boolean;
}

export type FieldValue = string | number | boolean | null | undefined | Dayjs;

export interface Template {
  about: string;
  fields: Field[];
}

export type Column = {
  key: string;
  label: string;
  icon?: string;
  align?: string;
  width?: string;
  text?: string;
};

export type File = {
  file_name: string;
  name: string;
  file_url: string;
  is_private: boolean;
  attached_to_doctype?: string;
  attached_to_field?: string;
  attached_to_name?: string;
};

export type Notification = {
  creation: string;
  name: string;
  notification_type: string;
  read: boolean;
  reference_comment: string;
  reference_ticket: string;
  user_from: UserInfo;
  user_to: UserInfo;
};

export type UserInfo = {
  email: string;
  image: string;
  name: string;
};

export interface RenderField {
  label: string;
  name: string;
  type: string;
  placeholder?: string;
  description?: string;
}

export interface EmailService {
  name: string;
  icon: string;
  info: string;
  link: string;
  custom: boolean;
}

export type EmailStep = "email-list" | "email-add" | "email-edit";

export interface EmailAccount {
  email_account_name: string;
  email_id: string;
  service: string;
  api_key?: string;
  api_secret?: string;
  password?: string;
  frappe_mail_site?: string;
  enable_outgoing?: boolean;
  enable_incoming?: boolean;
  default_outgoing?: boolean;
  default_incoming?: boolean;
}

export type TicketTab = "activity" | "email" | "comment" | "details" | "call";

export interface TabObject {
  name: TicketTab;
  label: string;
  icon: Component;
  condition?: () => boolean;
}

export interface RootCategory {
  category_id: string;
  category_name: string;
}

export interface Article {
  name: string;
  title: string;
  category_name: string;
  category_id: string;
  published_on: string;
  author: Author;
  subtitle: string;
  article_image: string | null;
  _user_tags: string | null;
  status: string;
  creation: string;
  content: string;
  modified: string;
  feedback: FeedbackAction;
}

export type FeedbackAction = 0 | 1 | 2; // 0: neutral, 1: like, 2: dislike

export interface Author {
  name: string;
  image: string | null;
  email: string;
}

export interface Category {
  categoryName: string;
  articles: Article[];
  authors?: {
    [key: string]: Author;
  };
  children?: Article[];
}

export interface View {
  filters: string;
  order_by: string;
  columns: string;
  rows: string;
  dt?: string;
  type?: string;
  route_name?: string;
  user?: string;
  icon?: string;
  label?: string;
  is_default?: boolean;
  pinned?: boolean;
  public?: boolean;
  group_by_field?: string;
  name?: string;
  is_customer_portal?: boolean;
}

export interface ViewType {
  view_type: string;
  group_by_field: string;
  name: string;
}

export interface Breadcrumb {
  label: string;
  route?: {
    name: string;
    params?: Record<string, string>;
  };
}

// Activity Types
interface BaseActivity {
  type: string;
  key: string;
  creation: string;
  content: string;
}

interface HistoryActivity extends BaseActivity {
  type: "history";
  user: string;
  relatedActivities: HistoryActivity[];
}

export interface EmailActivity extends BaseActivity {
  type: "email";
  attachments: FileAttachment;
  bcc: string;
  cc: string;
  name: string;
  sender: { full_name: string; name: string };
  subject: string;
  to: string;
  isFirstEmail: boolean;
}

export interface CommentActivity extends BaseActivity {
  type: "comment";
  name: string;
  commenter: string;
  commentedBy: string;
  attachments: FileAttachment[];
}

export interface CallActivity extends BaseActivity {
  type: "call";
  name: string;
  caller: string;
  calledBy: string;
  attachments: FileAttachment[];
  call_type: "Incoming" | "Outgoing";
}

export interface FeedbackActivity {
  type: "feedback";
  feedback_rating: number;
  feedback: string; // option seletor
  feedback_extra?: string; // free flow text
  sender: { name: string; full_name: string };
  key: string;
}

export type TicketActivity =
  | HistoryActivity
  | EmailActivity
  | CommentActivity
  | CallActivity
  | FeedbackActivity;

interface FileAttachment {
  name: string;
  file_name: string;
  file_url: string;
}

export interface FieldCriteriaState {
  selectedParentField: string;
  selectedChildField: string;
  childFields: any[];
  parentFieldValues: any[];
  childFieldValues: any[];
  currentParentSelection: string;
  childSelections: any;
  initialChildSelections: any;
  parentSearch: string;
  childSearch: string;
  enabled: boolean;
}

interface ResourceBase {
  data: any;
  error: any;
  fetched: boolean;
  loading: boolean;
  params: any;
  previousData: any;
  promise: Promise<any> | null;
  submit: (params?: any) => void;
}

interface DocumentResourceOptions<T = unknown> {
  doctype: string;
  name: string;
  auto?: boolean;
  whitelistedMethods?: Record<string, string>;
  onError?: (error: any) => void;
  onSuccess?: (data: T) => void;
  transform?: (doc: T) => T;
  delete?: {
    onSuccess?: () => void;
    onError?: (error: any) => void;
  };
  setValue?: {
    onSuccess?: () => void;
    onError?: (error: any) => void;
  };
}

export interface DocumentResource<T = unknown> {
  // Configuration
  auto: boolean;
  doctype: string;
  name: string;
  isDirty: boolean;
  promise: Promise<void> | null;

  // Main document data
  doc: T;
  originalDoc: T;

  // Core methods
  reload(): void;
  update(options: Partial<DocumentResourceOptions<T>>): void;

  // Sub-resources
  get: ResourceBase & {
    data: T;
    params: {
      doctype: string;
      name: string;
    };
  };

  setValue: ResourceBase & {
    submit: (
      values: Partial<T>,
      options?: { onSuccess?: () => void; onError?: (error: any) => void }
    ) => void;
  };

  setValueDebounced: ResourceBase & {
    submit: (values: Partial<T>) => void;
  };

  save: ResourceBase;
  delete: ResourceBase;

  // Dynamic whitelisted methods
  [methodName: string]: any;
}

export interface Customizations {
  custom_fields: {
    fieldname: string;
    required: number;
    placeholder: string;
    url_method: string;
  }[];
  _form_script: string[];
  _customActions?: any;
  _customOnChange?: any;
}

export interface TicketContact {
  name: string;
  email_id: string;
  phone: string;
  mobile_no: string;
  image: string;
}

export type RecentTicket = Record<
  "subject" | "status" | "priority" | "name",
  string | number
>;
export type SimilarTicket = Record<
  "subject" | "status" | "priority" | "name",
  string | number
>;
export interface RecentSimilarTicket {
  recent_tickets: RecentTicket[];
  similar_tickets: SimilarTicket[];
}

export interface TicketActivities {
  comments: Comment[];
  communications: Communication[];
  history: Activity[];
  views: ViewLog[];
}

// symbols
export const TicketSymbol: InjectionKey<
  ComputedRef<DocumentResource<HDTicket>>
> = Symbol("ticket");
export const AssigneeSymbol: InjectionKey<
  ComputedRef<Resource<Record<"name", string>[]>>
> = Symbol("assignees");

export const CustomizationSymbol: InjectionKey<
  ComputedRef<Resource<Customizations>>
> = Symbol("customizations");

export const TicketContactSymbol: InjectionKey<
  ComputedRef<Resource<TicketContact>>
> = Symbol("ticketContact");

export const RecentSimilarTicketsSymbol: InjectionKey<
  ComputedRef<Resource<RecentSimilarTicket>>
> = Symbol("recentSimilarTickets");

export const ActivitiesSymbol: InjectionKey<
  ComputedRef<Resource<TicketActivities>>
> = Symbol("activities");

declare global {
  interface Window {
    is_fc_site: boolean;
    date_format: string;
    time_format: string;
    session_user: string;
  }
}
