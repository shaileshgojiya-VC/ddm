import ProductPricingCard from "@/components/core/products/product-pricing-card";
import NoDataFound from "@/components/core/no-data-found";
import { Supplier } from "@/types/supplier";

interface ProductsPricingTabProps {
  readonly supplierDetails: Supplier;
}
export default function ProductsPricingTab({
  supplierDetails,
}: ProductsPricingTabProps) {
  const products = supplierDetails?.product_details || [];

  if (products?.length === 0) {
    return (
      <NoDataFound
        title="No products found"
        description="This supplier has not added any products yet."
      />
    );
  }
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3  gap-4">
      {products?.map((product) => (
        <ProductPricingCard key={product?.id} product={product} />
      ))}
    </div>
  );
}
