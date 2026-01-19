import InquiryFilters from "@/components/core/inquiry/inquiry-filters";
import InquiryTable from "@/components/core/inquiry/inquiry-table";
import InquiryTabs from "@/components/core/inquiry/inquiry-tabs";
import PageHeading from "@/components/core/page-heading";
import Pagination from "@/components/core/pagination";
import SuspenseLoader from "@/components/core/suspense-loader";
import type { InquiriesSearchParams } from "@/types/inquiry";
import { getInquiries } from "@/lib/data";
import { Suspense } from "react";

interface InquiryManagementPageProps {
  readonly searchParams: Promise<InquiriesSearchParams>;
}

export default async function InquiryManagementPage({
  searchParams,
}: InquiryManagementPageProps) {
  const resolvedSearchParams = await searchParams;
  const { inquiries, pagination, dataCount } = await getInquiries(
    resolvedSearchParams
  );

  return (
    <div className="space-y-6">
      <PageHeading
        title="Inquiry Management"
        description="View and manage all inquiries"
      />

      {/* Filters Section */}
      <Suspense fallback={<SuspenseLoader title="Loading filters..." />}>
        <InquiryFilters />
      </Suspense>

      {/* Tab Navigation */}
      <Suspense fallback={<SuspenseLoader title="Loading tabs..." />}>
        <InquiryTabs dataCount={dataCount ?? {}} />
      </Suspense>

      {/* Inquiry Table */}
      <InquiryTable inquiries={inquiries} />

      {/* Pagination */}
      <Pagination pagination={pagination} />
    </div>
  );
}
