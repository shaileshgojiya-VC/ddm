import { Briefcase, Building2, Calendar, FileText, Mail } from "lucide-react";
import Link from "next/link";

import BackButton from "@/components/core/back-button";
import NoDataFound from "@/components/core/no-data-found";
import PageHeading from "@/components/core/page-heading";
import PhaseBadge from "@/components/core/phase-badge";
import StageBadge from "@/components/core/stage-badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getUserDetails } from "@/lib/data";
import { getRoleBadgeStyle } from "@/utils/role-styles";
import { formatDate } from "@/utils/date-format";

interface UserDetailsPageProps {
  readonly params: Promise<{ id: string }>;
}

export default async function UserDetailsPage({
  params,
}: UserDetailsPageProps) {
  const { id } = await params;
  const userDetails = await getUserDetails(id);
  const {
    name,
    email,
    role,
    joined_at,
    total_inquiry,
    active_deals,
    deals_won,
    inquiries,
  } = userDetails || {};
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <BackButton />
        <PageHeading
          title="User Details"
          description="View user profile and activity"
        />
      </div>
      {userDetails ? (
        <div className="grid gap-6 xl:grid-cols-3">
          <Card className="">
            <CardContent className="pt-6">
              <div className="flex flex-col items-center space-y-3">
                <Avatar className="size-20 bg-primary">
                  <AvatarFallback className="bg-primary text-white text-3xl font-semibold">
                    {name?.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>

                <h2 className="text-2xl font-semibold capitalize">
                  {name || "-"}
                </h2>

                <Badge className={getRoleBadgeStyle(role?.name || "")}>
                  {role?.name || "-"}
                </Badge>

                <div className="w-full space-y-3 pt-2">
                  <div className="flex items-center gap-3 text-muted-foreground">
                    <Mail className="size-4 shrink-0" />
                    <span className="text-sm">
                      {email ? (
                        <Link
                          href={`mailto:${email}`}
                          target="_blank"
                          className="text-primary"
                        >
                          {email}
                        </Link>
                      ) : (
                        "-"
                      )}
                    </span>
                  </div>

                  <div className="flex items-start gap-3 text-muted-foreground">
                    <Building2 className="size-4 shrink-0 mt-0.5" />
                    <span className="text-sm">{role?.description || "-"}</span>
                  </div>

                  <div className="flex items-center gap-3 text-muted-foreground">
                    <Calendar className="size-4 shrink-0" />
                    <span className="text-sm">
                      Last active: {joined_at ? formatDate(joined_at) : "-"}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="space-y-6 xl:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Activity Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-3 mb-6">
                  <Card className="bg-muted border-0 shadow-none">
                    <CardContent className="flex flex-col items-center justify-center">
                      <FileText className="size-5 text-muted-foreground mb-2" />
                      <p className="text-3xl font-bold">{total_inquiry || 0}</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        Total Inquiries
                      </p>
                    </CardContent>
                  </Card>

                  <Card className="bg-muted border-0 shadow-none">
                    <CardContent className="flex flex-col items-center justify-center">
                      <Briefcase className="size-5 text-muted-foreground mb-2" />
                      <p className="text-3xl font-bold">{active_deals || 0}</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        Active Deals
                      </p>
                    </CardContent>
                  </Card>

                  <Card className="bg-green-100 border-0 shadow-none">
                    <CardContent className="flex flex-col items-center justify-center">
                      <Briefcase className="size-5 text-green-600 mb-2" />
                      <p className="text-3xl font-bold text-green-700">
                        {deals_won || 0}
                      </p>
                      <p className="text-sm text-green-600 mt-1">Deals Won</p>
                    </CardContent>
                  </Card>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Recent Inquiries</h3>
                  {inquiries && inquiries.length > 0 ? (
                    <div className="space-y-2 w-full max-h-[400px] overflow-y-auto">
                      {inquiries.map((inquiry) => (
                        <Link
                          key={inquiry?.id}
                          href={`/inquiry-management/${inquiry?.id}/view`}
                          className="flex flex-wrap items-center justify-between p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors gap-3 w-full overflow-hidden"
                        >
                          <PhaseBadge phase={inquiry?.phase || "-"} />
                          <div className="flex-1">
                            <p className="font-semibold text-sm">
                              {inquiry?.company_name || "-"}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {inquiry?.customer_name || "-"}
                            </p>
                          </div>
                          <StageBadge stage={inquiry?.stage || "-"} />
                        </Link>
                      ))}
                    </div>
                  ) : (
                    <NoDataFound
                      title="No inquiries found"
                      description="No inquiries found for this user"
                      icon={FileText}
                    />
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      ) : (
        <NoDataFound
          title="User not found"
          description="The user you are looking for does not exist."
        />
      )}
    </div>
  );
}
