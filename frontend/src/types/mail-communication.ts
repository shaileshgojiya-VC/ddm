export interface MailCommunication {
  id: string;
  to_person_name: string;
  to_person_email: string[];
  from_person_email: string;
  subject: string;
  content: string;
  mail_type: "received" | "sent";
  status: string;
  created_at: string;
  received_at: string;
  updated_at: string;
}
