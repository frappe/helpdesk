import { Component } from "vue";

export interface Resource<T = unknown> {
  auto: boolean;
  loading: boolean;
  data: T;
  pageLength: number;
  totalCount: number;
  hasNextPage: boolean;
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
  hide_from_customer: 0 | 1;
  label: string;
  options: string;
  required: 0 | 1;
  description?: null;
  url_method?: string;
  link_filters?: string;
  filters?: string;
  display_via_depends_on?: string;
  mandatory_via_depends_on?: string;
}

export type FieldValue = string | number | boolean;

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

export type TicketTab = "activity" | "email" | "comment" | "details";

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

export type TicketActivity = HistoryActivity | EmailActivity | CommentActivity;

interface FileAttachment {
  name: string;
  file_name: string;
  file_url: string;
}

declare global {
  interface Window {
    sysdefaults: {
      app_name: string;
      enable_onboarding: string;
      setup_complete: string;
      disable_document_sharing: string;
      time_format: string;
      use_number_format_from_currency: string;
      first_day_of_the_week: string;
      currency_precision: string;
      apply_strict_user_permissions: string;
      allow_older_web_view_links: string;
      session_expiry: string;
      document_share_key_expiry: string;
      deny_multiple_sessions: string;
      disable_user_pass_login: string;
      allow_login_using_mobile_number: string;
      allow_login_using_user_name: string;
      login_with_email_link: string;
      login_with_email_link_expiry: string;
      allow_consecutive_login_attempts: string;
      allow_login_after_fail: string;
      enable_two_factor_auth: string;
      bypass_2fa_for_retricted_ip_users: string;
      bypass_restrict_ip_check_if_2fa_enabled: string;
      two_factor_method: string;
      otp_issuer_name: string;
      logout_on_password_reset: string;
      reset_password_link_expiry_duration: string;
      password_reset_limit: string;
      enable_password_policy: string;
      minimum_password_score: string;
      email_retry_limit: string;
      disable_standard_email_footer: string;
      hide_footer_in_auto_email_reports: string;
      attach_view_link: string;
      store_attached_pdf_document: string;
      allow_guests_to_upload_files: string;
      force_web_capture_mode_for_uploads: string;
      strip_exif_metadata_from_uploaded_images: string;
      disable_system_update_notification: string;
      disable_change_log_notification: string;
      hide_empty_read_only_fields: string;
      backup_limit: string;
      encrypt_backup: string;
      max_auto_email_report_per_user: string;
      max_report_rows: string;
      dormant_days: string;
      allow_error_traceback: string;
      link_field_results_limit: string;
      country: string;
      language: string;
      time_zone: string;
      currency: string;
      date_format: string;
      number_format: string;
      float_precision: string;
      rounding_method: string;
      enable_scheduler: string;
      enable_telemetry: string;
      lang: string;
      desktop: {
        home_page: string;
      };
      user: string;
      owner: string;
    };
  }
}
