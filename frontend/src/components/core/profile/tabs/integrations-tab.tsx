import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ExternalLink } from "lucide-react";

export default function IntegrationsTab() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <CardTitle className="text-2xl font-semibold">
              Microsoft Account
            </CardTitle>
          </div>
          <CardDescription>
            Connect your Microsoft account to send email replies directly from
            inquiries
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Microsoft Account Connection Card */}
          <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-4">
              <div className="flex items-center justify-center size-10 rounded-lg bg-muted">
                <svg
                  viewBox="0 0 23 23"
                  className="size-5 text-muted-foreground fill-current"
                >
                  <path d="M0 0h11v11H0zM12 0h11v11H12zM0 12h11v11H0zM12 12h11v11H12z" />
                </svg>
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <p className="font-semibold">Microsoft Account</p>
                  <Badge variant="secondary">Not Connected</Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  Connect to enable email features
                </p>
              </div>
            </div>
            <Button variant="default" size="sm">
              Connect Account
              <ExternalLink className="ml-2 size-4" />
            </Button>
          </div>

          {/* Why Connect Section */}
          <div className="space-y-3 border border-dashed rounded-lg p-4">
            <h3 className="font-semibold">Why connect?</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="mt-2 size-1 rounded-full bg-muted-foreground shrink-0" />
                <span>
                  Reply to customer inquiries directly from this portal
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-2 size-1 rounded-full bg-muted-foreground shrink-0" />
                <span>Use AI-generated email suggestions</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-2 size-1 rounded-full bg-muted-foreground shrink-0" />
                <span>Keep all communications in one place</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-2 size-1 rounded-full bg-muted-foreground shrink-0" />
                <span>Automatic tracking of sent messages</span>
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
