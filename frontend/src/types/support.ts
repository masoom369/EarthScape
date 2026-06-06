export interface SupportTicket {
  id: string;
  subject: string;
  description: string;
  screenshot_url?: string;
  status: string;
  response?: string;
  responded_by?: string;
  responded_at?: string;
  submitted_by: string;
  created_at: string;
  updated_at: string;
}
