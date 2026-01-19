import ProductCard from "@/components/core/products/product-card";

import NoDataFound from "@/components/core/no-data-found";
import ProductListItem from "@/components/core/products/product-list-item";
import { Product } from "@/types/product";

interface ProductListProps {
  readonly products: Product[];
  readonly view?: "grid" | "list";
}

export default function ProductList({
  products,
  view = "grid",
}: ProductListProps) {
  if (products.length === 0) {
    return (
      <NoDataFound
        title="No products found in this category"
        description="Try adjusting your search or filter to find what you're looking for."
      />
    );
  }

  if (view === "list") {
    return (
      <div className="space-y-3">
        <ProductListItem products={products} />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2 2xl:grid-cols-3">
      {products?.map((product) => (
        <ProductCard key={product?.id} product={product} />
      ))}
    </div>
  );
}
