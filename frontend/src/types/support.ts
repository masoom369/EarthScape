export type TicketStatus = "open" | "in-progress" | "resolved";

export interface SupportTicket {
  id: string;
  subject: string;
  description: string;
  screenshot_url: string | null;
  status: TicketStatus;
  response: string | null;
  responded_by: string | null;
  responded_at: string | null;
  submitted_by: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedTickets {
  items: SupportTicket[];
  total: number;
  page: number;
  limit: number;
}