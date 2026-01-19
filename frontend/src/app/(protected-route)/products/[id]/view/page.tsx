import ProductView from "@/components/core/product-details/product-view";
import { getProductDetails } from "@/lib/data";

interface ProductViewPageProps {
  readonly params: Promise<{ id: string }>;
}

export default async function ProductViewPage({
  params,
}: ProductViewPageProps) {
  const { id } = await params;

  const productDetails = await getProductDetails(id);

  return <ProductView productDetails={productDetails} mode="view" />;
}
