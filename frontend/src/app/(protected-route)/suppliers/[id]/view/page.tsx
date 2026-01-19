import SupplierView from "@/components/core/supplier-details/supplier-view";
import { getSupplierDetails } from "@/lib/data";

interface SupplierViewPageProps {
  readonly params: Promise<{ id: string }>;
}

export default async function SupplierViewPage({
  params,
}: SupplierViewPageProps) {
  const { id } = await params;

  const supplierDetails = await getSupplierDetails(id);

  return <SupplierView supplierDetails={supplierDetails} mode="view" />;
}
