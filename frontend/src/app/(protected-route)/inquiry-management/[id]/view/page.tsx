import BackButton from "@/components/core/back-button";
import CommonTabs, { type TabItem } from "@/components/core/common-tabs";
import InquiryBasicDetails from "@/components/core/inquiry-details/inquiry-basic-details";
import InquiryProgress from "@/components/core/inquiry-details/inquiry-progress";
import BuyerCommunicationTab from "@/components/core/inquiry-details/tabs/buyer-communication-tab";
import DocumentsTab from "@/components/core/inquiry-details/tabs/documents-tab";
import OverviewTab from "@/components/core/inquiry-details/tabs/overview-tab";
import TeamChatTab from "@/components/core/inquiry-details/tabs/team-chat-tab";
import TeamMembers from "@/components/core/inquiry-details/team-members";
import PhaseBadge from "@/components/core/phase-badge";
import PriorityBadge from "@/components/core/priority-badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { getInquiryDetails } from "@/lib/data";
import { Check, ExternalLink, Globe, Mail } from "lucide-react";
import Link from "next/link";

interface InquiryDetailsPageProps {
  readonly params: Promise<{ id: string }>;
}

export default async function InquiryDetailsPage({
  params,
}: InquiryDetailsPageProps) {
  const { id } = await params;
  const inquiryDetails = await getInquiryDetails(id);
  const {
    phase,
    priority,
    customer_country,
    name,
    customer_email,
    company_name,
    bitrix_url,
  } = inquiryDetails || {};

  const tabs: TabItem[] = [
    {
      value: "overview",
      label: "Overview",
      content: <OverviewTab inquiryDetails={inquiryDetails} />,
    },
    {
      value: "buyer-communication",
      label: "Buyer Communication",
      content: <BuyerCommunicationTab inquiryDetails={inquiryDetails} />,
    },
    {
      value: "team-chat",
      label: "Team Chat",
      content: <TeamChatTab />,
    },
    {
      value: "documents",
      label: "Documents",
      content: <DocumentsTab inquiryDetails={inquiryDetails} />,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-start gap-3 flex-1">
          <BackButton />
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <PhaseBadge phase={phase || "-"} />
              <PriorityBadge priority={priority || "-"} />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">{name || "-"}</h1>
            <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <span className="font-medium text-foreground">
                {company_name || "-"}
              </span>
              <span className="flex items-center gap-1.5">
                <Mail className="size-4 shrink-0" />
                {customer_email ? (
                  <Link
                    href={`mailto:${customer_email}`}
                    target="_blank"
                    className="text-primary"
                  >
                    {customer_email}
                  </Link>
                ) : (
                  "-"
                )}
              </span>
              <span className="flex items-center gap-1.5">
                <Globe className="size-4 shrink-0" />
                {customer_country || "-"}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {phase === "lead" ? (
            <>
              <Button variant="outline" className="gap-2" disabled>
                <ExternalLink className="size-4" />
                Sync to Bitrix
              </Button>
              <Button
                className="gap-2 bg-green-600 hover:bg-green-700"
                disabled
              >
                <Check className="size-4" />
                Convert to Deal
              </Button>
            </>
          ) : (
            <Button variant="outline" className="gap-2" asChild>
              <Link href={bitrix_url || "#"} target="_blank">
                <ExternalLink className="size-4" />
                View in Bitrix
              </Link>
            </Button>
          )}
        </div>
      </div>
      <InquiryProgress inquiryDetails={inquiryDetails} />
      <Separator />
      <InquiryBasicDetails inquiryDetails={inquiryDetails} />
      <TeamMembers inquiryDetails={inquiryDetails} />
      <CommonTabs tabs={tabs} defaultValue="overview" />
    </div>
  );
}
