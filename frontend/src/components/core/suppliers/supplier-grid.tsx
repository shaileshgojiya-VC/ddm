import type { Supplier } from "@/types/supplier";
import NoDataFound from "@/components/core/no-data-found";
import SupplierCard from "./supplier-card";

interface SupplierGridProps {
  readonly suppliers: Supplier[];
}

export default function SupplierGrid({ suppliers }: SupplierGridProps) {
  if (!suppliers || suppliers?.length === 0) {
    return <NoDataFound title="No suppliers found" />;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
      {suppliers?.map((supplier) => (
        <SupplierCard key={supplier?.id} supplier={supplier} />
      ))}
    </div>
  );
}
