import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { MailCommunication } from "@/types/mail-communication";
import { formatDate } from "@/utils/date-format";
import { Mail } from "lucide-react";
import HtmlViewer from "@/components/core/html-viewer";

interface EmailCardProps {
  readonly email: MailCommunication;
}

export default function EmailCard({ email }: EmailCardProps) {
  const isReceived = email?.mail_type === "received";

  return (
    <Card
      className={cn("p-4", {
        "bg-muted/30": isReceived,
        "bg-primary/10 dark:bg-primary/20": !isReceived,
      })}
    >
      <div className="flex items-start gap-4">
        {/* Mail Icon */}
        <div
          className={cn(
            "flex size-10 shrink-0 items-center justify-center rounded-full",
            {
              "bg-muted": isReceived,
              "bg-primary/10": !isReceived,
            }
          )}
        >
          <Mail
            className={cn("size-5", {
              "text-muted-foreground": isReceived,
              "text-primary": !isReceived,
            })}
          />
        </div>

        {/* Email Content */}
        <div className="flex-1 min-w-0 space-y-2">
          {/* Header */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap text-sm">
                <span className="font-medium text-muted-foreground">
                  {isReceived ? "From:" : "To:"}
                </span>
                <span className="font-semibold truncate">
                  {isReceived
                    ? email?.from_person_email
                    : email?.to_person_name ||
                      email?.to_person_email?.join(", ")}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {email?.received_at ? formatDate(email?.received_at) : "-"}
              </p>
            </div>
            <Badge
              variant={isReceived ? "secondary" : "default"}
              className={cn("bg-secondary", {
                "bg-primary": !isReceived,
              })}
            >
              {isReceived ? "Received" : "Sent"}
            </Badge>
          </div>

          {/* Subject */}
          <div>
            <h4 className="font-semibold text-base">
              Re: {email?.subject || "-"}
            </h4>
          </div>

          {/* Email Content */}
          <HtmlViewer html={email?.content || ""} />
        </div>
      </div>
    </Card>
  );
}
