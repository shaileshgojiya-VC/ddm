import PageHeading from "@/components/core/page-heading";
import Pagination from "@/components/core/pagination";
import SupplierFilters from "@/components/core/suppliers/supplier-filters";
import SupplierGrid from "@/components/core/suppliers/supplier-grid";
import SupplierTable from "@/components/core/suppliers/supplier-table";
import SuspenseLoader from "@/components/core/suspense-loader";
import ViewToggle from "@/components/core/view-toggle";
import type { SuppliersSearchParams } from "@/types/supplier";
import { getSuppliers } from "@/lib/data";
import { Suspense } from "react";

interface SuppliersPageProps {
  readonly searchParams: Promise<SuppliersSearchParams>;
}

export default async function SuppliersPage({
  searchParams,
}: SuppliersPageProps) {
  const resolvedSearchParams = await searchParams;
  const { suppliers, pagination } = await getSuppliers(resolvedSearchParams);

  const view = resolvedSearchParams.view || "grid";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-4 items-start justify-between">
        <PageHeading
          title="Suppliers"
          description="Dana Dairy supplier network"
        />
        <ViewToggle />
      </div>

      <Suspense
        fallback={<SuspenseLoader title="Loading suppliers filters..." />}
      >
        <SupplierFilters />
      </Suspense>

      {/* Showing count */}
      {pagination && (
        <div className="text-sm text-muted-foreground">
          Showing {suppliers?.length} of {pagination?.total} suppliers
        </div>
      )}

      {/* Grid or List View */}
      {view === "grid" ? (
        <SupplierGrid suppliers={suppliers} />
      ) : (
        <SupplierTable suppliers={suppliers} />
      )}

      <Pagination pagination={pagination} />
    </div>
  );
}
