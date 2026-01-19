import { Inquiry } from "@/types/inquiry";
import EmailCommunication from "@/components/core/email-communication";

interface BuyerCommunicationTabProps {
  readonly inquiryDetails: Inquiry;
}

export default function BuyerCommunicationTab({
  inquiryDetails,
}: BuyerCommunicationTabProps) {
  const { mail_communication, company_name } = inquiryDetails || {};

  return (
    <EmailCommunication
      mail_communication={mail_communication || []}
      company_name={company_name || ""}
    />
  );
}
