import { Barcode, Building2 } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

import type { Product } from "@/types/product";
import NoDataFound from "@/components/core/no-data-found";

interface ProductListItemProps {
  readonly products: Product[];
}

export default function ProductListItem({ products }: ProductListItemProps) {
  if (!products || products?.length === 0) {
    return (
      <NoDataFound
        title="No products found in this category"
        description="Try adjusting your search or filter to find what you're looking for."
      />
    );
  }

  return (
    <Card className="py-0">
      <CardContent className="divide-y p-0">
        {products?.map((product) => {
          const {
            image_url,
            category,
            name,
            description,
            primary_supplier_name,
            price,
            currency_id,
            sku_id,
            hs_code,
            units_per_carton,
          } = product;

          return (
            <Link
              href={`/products/${product.id}/view`}
              key={product.id}
              className="flex xl:flex-nowrap flex-wrap flex-col md:flex-row md:items-center justify-between p-4 hover:bg-muted/50 transition-colors cursor-pointer md:gap-4 gap-3 group"
            >
              {/* Product Image */}
              <div className="relative size-20 shrink-0 overflow-hidden rounded-lg bg-muted order-1">
                <Image
                  src={image_url || "/images/danadairy.png"}
                  alt={name || "Product Image"}
                  fill
                  sizes="100px"
                  loading="eager"
                  className="object-cover transition-transform group-hover:scale-105"
                />
              </div>

              {/* Product Info */}
              <div className="flex flex-col justify-between gap-2 xl:order-2 order-3 w-full flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-foreground transition-colors group-hover:text-primary">
                    {name || "-"}
                  </h3>
                  <Badge variant="secondary" className="text-xs">
                    {category || "-"}
                  </Badge>
                </div>
                <p className="line-clamp-1 text-sm text-muted-foreground">
                  {description || "-"}
                </p>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Barcode className="size-3" />
                    <span>{sku_id || "-"}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs">HS:</span>
                    <span>{hs_code || "-"}</span>
                  </div>
                  <span>{units_per_carton || "-"} units/carton</span>
                  <div className="flex items-center gap-1">
                    <Building2 className="size-3" />
                    <span>{primary_supplier_name || "-"}</span>
                  </div>
                </div>
              </div>

              {/* Price & MOQ */}
              <div className="flex shrink-0 flex-col items-end justify-center gap-1 xl:order-3 order-2">
                <div className="font-bold text-primary">
                  {currency_id || "-"} {price || "-"}
                </div>
              </div>
            </Link>
          );
        })}
      </CardContent>
    </Card>
  );
}
