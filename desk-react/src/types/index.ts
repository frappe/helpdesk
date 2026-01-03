// Core entity types
export interface User {
  name: string;
  email: string;
  full_name: string;
  user_image?: string;
  user_type: 'Agent' | 'Customer';
}

export interface Ticket {
  name: string;
  subject: string;
  status: string;
  priority?: string;
  ticket_type?: string;
  description?: string;
  raised_by?: string;
  customer?: string;
  contact?: string;
  agent_group?: string;
  assigned_to?: string;
  resolution?: string;
  creation: string;
  modified: string;
  response_by?: string;
  resolution_by?: string;
  first_responded_on?: string;
  resolution_date?: string;
  _assign?: string;
}

export interface TicketComment {
  name: string;
  content: string;
  commented_by: string;
  creation: string;
  is_pinned?: boolean;
  attachments?: Attachment[];
}

export interface Attachment {
  name: string;
  file_name: string;
  file_url: string;
  file_size: number;
}

export interface Agent {
  name: string;
  agent_name: string;
  user: string;
  email?: string;
  teams?: string[];
  is_active: boolean;
}

export interface Team {
  name: string;
  team_name: string;
  description?: string;
  members?: TeamMember[];
}

export interface TeamMember {
  agent: string;
  agent_name: string;
}

export interface Customer {
  name: string;
  customer_name: string;
  email?: string;
  mobile_no?: string;
  primary_contact?: string;
}

export interface Article {
  name: string;
  title: string;
  content: string;
  category: string;
  author: string;
  status: 'Published' | 'Draft';
  creation: string;
  modified: string;
}

export interface KnowledgeBase {
  name: string;
  category_name: string;
  description?: string;
  parent_category?: string;
}

export interface DashboardMetrics {
  total_tickets: number;
  open_tickets: number;
  resolved_tickets: number;
  avg_response_time: number;
  avg_resolution_time: number;
  satisfaction_score?: number;
}

export interface ApiResponse<T> {
  message: T;
}

export interface ListResponse<T> {
  data: T[];
  total_count: number;
}
