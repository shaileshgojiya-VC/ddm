import { Mail, MapPin, Phone, Building2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import DataTable, { type Column } from "@/components/core/data-table";
import type { Supplier } from "@/types/supplier";
import Link from "next/link";
import { formatDate } from "@/utils/date-format";

interface SupplierTableProps {
  readonly suppliers: Supplier[];
}

// Cell renderer components
function SupplierCell({ supplier }: { readonly supplier: Supplier }) {
  return (
    <Link
      href={`/suppliers/${supplier?.id}/view`}
      className="flex items-center gap-3"
    >
      <div className="flex items-center justify-center size-10 rounded-lg bg-primary/10 shrink-0">
        <Building2 className="size-5 text-primary" />
      </div>
      <div>
        <p className="font-medium">{supplier?.company_name || "-"}</p>
        <p className="text-xs text-muted-foreground">
          {supplier?.address || "-"}
        </p>
      </div>
    </Link>
  );
}

function TypeCell({ supplier }: { readonly supplier: Supplier }) {
  return <Badge variant="secondary">{supplier?.company_type || "-"}</Badge>;
}

function CountryCell({ supplier }: { readonly supplier: Supplier }) {
  return (
    <div className="flex items-center gap-2">
      <MapPin className="size-4 shrink-0 text-muted-foreground" />
      <span>{supplier?.country || "-"}</span>
    </div>
  );
}

function CategoriesCell({ supplier }: { readonly supplier: Supplier }) {
  return (
    <>
      {supplier?.category?.length > 0 ? (
        <div className="flex items-center gap-1 flex-wrap">
          {supplier?.category?.map((category) => (
            <Badge key={category} variant="outline">
              {category}
            </Badge>
          ))}
        </div>
      ) : (
        "-"
      )}
    </>
  );
}

function ContactCell({ supplier }: { readonly supplier: Supplier }) {
  return (
    <div className="space-y-1 text-sm">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Mail className="size-3.5 shrink-0" />
        <span className="truncate max-w-[180px]">{supplier?.email || "-"}</span>
      </div>
      <div className="flex items-center gap-2 text-muted-foreground">
        <Phone className="size-3.5 shrink-0" />
        <span>{supplier?.phone_number || "-"}</span>
      </div>
    </div>
  );
}

function LastContactCell({ supplier }: { readonly supplier: Supplier }) {
  return (
    <span className="text-sm">
      {supplier?.last_contact ? formatDate(supplier?.last_contact) : "-"}
    </span>
  );
}

const columns: Column<Supplier>[] = [
  {
    header: "Supplier",
    cell: (supplier) => <SupplierCell supplier={supplier} />,
  },
  {
    header: "Type",
    cell: (supplier) => <TypeCell supplier={supplier} />,
  },
  {
    header: "Country",
    cell: (supplier) => <CountryCell supplier={supplier} />,
  },
  {
    header: "Categories",
    cell: (supplier) => <CategoriesCell supplier={supplier} />,
  },
  {
    header: "Contact",
    cell: (supplier) => <ContactCell supplier={supplier} />,
  },
  {
    header: "Last Contact",
    cell: (supplier) => <LastContactCell supplier={supplier} />,
  },
];

export default function SupplierTable({ suppliers }: SupplierTableProps) {
  return (
    <DataTable
      data={suppliers || []}
      columns={columns}
      getRowKey={(supplier) => supplier.id}
      emptyMessage="No suppliers found"
    />
  );
}
