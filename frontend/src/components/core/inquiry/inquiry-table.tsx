import DataTable, { type Column } from "@/components/core/data-table";
import PhaseBadge from "@/components/core/phase-badge";
import PriorityBadge from "@/components/core/priority-badge";
import StageBadge from "@/components/core/stage-badge";
import StatusBadge from "@/components/core/status-badge";
import type { Inquiry } from "@/types/inquiry";
import { formatDate } from "@/utils/date-format";
import { Calendar, User } from "lucide-react";
import Link from "next/link";

interface InquiryTableProps {
  readonly inquiries: Inquiry[];
}

// Cell renderer components
function IdBuyerCell({ inquiry }: { readonly inquiry: Inquiry }) {
  return (
    <Link
      href={`/inquiry-management/${inquiry.id}/view`}
      className="block space-y-1.5"
    >
      <div className="flex items-center gap-2">
        <PhaseBadge phase={inquiry?.phase} />
        <span className="text-xs font-medium text-primary">
          {inquiry?.name || "-"}
        </span>
      </div>
      <p className="font-medium text-sm">
        {inquiry?.customer_company_name || "-"}
      </p>
      <p className="text-xs text-muted-foreground">
        {inquiry?.customer_full_name || "-"}
      </p>
    </Link>
  );
}

function ProductCell({ inquiry }: { readonly inquiry: Inquiry }) {
  return <div className="text-sm">{inquiry?.prodcut_category || "-"}</div>;
}

function CountryCell({ inquiry }: { readonly inquiry: Inquiry }) {
  return <>{inquiry?.customer_country || "-"}</>;
}

function StageCell({ inquiry }: { readonly inquiry: Inquiry }) {
  return <StageBadge stage={inquiry?.stage_name || "-"} />;
}

function StatusCell({ inquiry }: { readonly inquiry: Inquiry }) {
  return <StatusBadge status={inquiry?.status || "-"} />;
}

function AssignedCell({ inquiry }: { readonly inquiry: Inquiry }) {
  return (
    <div className="flex items-center gap-2">
      <User className="size-3.5 text-muted-foreground shrink-0" />
      <span className="text-sm">{inquiry?.assigned_to || "-"}</span>
    </div>
  );
}

function PriorityCell({ inquiry }: { readonly inquiry: Inquiry }) {
  return <PriorityBadge priority={inquiry?.priority?.toLowerCase() || "-"} />;
}

function UpdatedCell({ inquiry }: { readonly inquiry: Inquiry }) {
  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <Calendar className="size-3.5 shrink-0" />
      <span>{inquiry?.updated_at ? formatDate(inquiry?.updated_at) : "-"}</span>
    </div>
  );
}

const columns: Column<Inquiry>[] = [
  {
    header: "ID / Buyer",
    cell: (inquiry) => <IdBuyerCell inquiry={inquiry} />,
  },
  {
    header: "Product",
    cell: (inquiry) => <ProductCell inquiry={inquiry} />,
  },
  {
    header: "Country",
    cell: (inquiry) => <CountryCell inquiry={inquiry} />,
  },
  {
    header: "Stage",
    cell: (inquiry) => <StageCell inquiry={inquiry} />,
  },
  {
    header: "Status",
    cell: (inquiry) => <StatusCell inquiry={inquiry} />,
  },
  {
    header: "Assigned",
    cell: (inquiry) => <AssignedCell inquiry={inquiry} />,
  },
  {
    header: "Priority",
    cell: (inquiry) => <PriorityCell inquiry={inquiry} />,
  },
  {
    header: "Updated",
    cell: (inquiry) => <UpdatedCell inquiry={inquiry} />,
  },
];

export default function InquiryTable({ inquiries }: InquiryTableProps) {
  return (
    <DataTable
      data={inquiries}
      columns={columns}
      getRowKey={(inquiry) => inquiry.id}
    />
  );
}
