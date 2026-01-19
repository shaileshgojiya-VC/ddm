import EmailCommunication from "@/components/core/email-communication";
import type { Supplier } from "@/types/supplier";

interface EmailCommunicationsTabProps {
  readonly supplierDetails: Supplier;
}

export default function EmailCommunicationsTab({
  supplierDetails,
}: EmailCommunicationsTabProps) {
  const { mail_communication, company_name } = supplierDetails || {};

  return (
    <EmailCommunication
      mail_communication={mail_communication || []}
      company_name={company_name || ""}
    />
  );
}
