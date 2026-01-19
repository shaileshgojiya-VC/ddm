import SupplierEdit from "@/components/core/supplier-details/supplier-edit";
import { getSupplierDetails } from "@/lib/data";

interface SupplierEditPageProps {
  readonly params: Promise<{ id: string }>;
}

export default async function SupplierEditPage({
  params,
}: SupplierEditPageProps) {
  const { id } = await params;

  const supplierDetails = await getSupplierDetails(id);

  return <SupplierEdit supplierDetails={supplierDetails} mode="edit" />;
}
