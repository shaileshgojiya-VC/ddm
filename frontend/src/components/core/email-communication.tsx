import EmailCard from "@/components/core/email-card";
import NoDataFound from "@/components/core/no-data-found";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MailCommunication } from "@/types/mail-communication";

interface EmailCommunicationProps {
  readonly mail_communication: MailCommunication[];
  readonly company_name: string;
}

export default function EmailCommunication({
  mail_communication,
  company_name,
}: EmailCommunicationProps) {
  // Sort emails by date (newest first)
  const sortedEmails = mail_communication
    ? [...mail_communication].sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
    : [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Email Communications</CardTitle>
        <p className="text-sm text-muted-foreground">
          Email conversation history with {company_name || ""}
        </p>
      </CardHeader>
      <CardContent className="space-y-3 max-h-[500px] overflow-y-auto">
        {sortedEmails?.length > 0 ? (
          <>
            {sortedEmails?.map((email) => (
              <EmailCard key={email?.id} email={email} />
            ))}
          </>
        ) : (
          <NoDataFound
            title="No email communications"
            description="Email conversation history will appear here once available"
          />
        )}
      </CardContent>
    </Card>
  );
}
