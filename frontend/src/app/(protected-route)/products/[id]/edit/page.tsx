import ProductEdit from "@/components/core/product-details/product-edit";
import { getProductDetails } from "@/lib/data";

interface ProductEditPageProps {
  readonly params: Promise<{ id: string }>;
}

export default async function ProductEditPage({
  params,
}: ProductEditPageProps) {
  const { id } = await params;

  const productDetails = await getProductDetails(id);

  return <ProductEdit productDetails={productDetails} mode="edit" />;
}
