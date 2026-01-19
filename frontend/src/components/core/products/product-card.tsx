import { Barcode, Building2 } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

import { Separator } from "@/components/ui/separator";
import type { Product } from "@/types/product";

interface ProductCardProps {
  readonly product: Product;
}

export default function ProductCard({ product }: ProductCardProps) {
  const {
    image_url,
    category,
    name,
    description,
    primary_supplier_name,
    price,
    currency_id,
    sku_id,
  } = product;

  return (
    <Link href={`/products/${product.id}/view`}>
      <Card className="group overflow-hidden transition-all hover:shadow-lg py-0 gap-0 min-h-full">
        {/* Product Image */}
        <div className="relative aspect-video overflow-hidden bg-muted">
          <Image
            src={image_url || "/images/danadairy.png"}
            alt="Product Image"
            fill
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            loading="eager"
            className="object-cover transition-transform group-hover:scale-105"
          />
        </div>

        <CardContent className="space-y-2 p-4">
          <Badge variant="secondary">{category || "-"}</Badge>
          <h3 className="font-semibold text-foreground transition-colors group-hover:text-primary">
            {name || "-"}
          </h3>
          {/* Product Description */}
          <p className="line-clamp-2 text-sm text-muted-foreground">
            {description || "-"}
          </p>

          {/* Supplier Info */}

          <div className="flex items-center gap-2">
            <Building2 className="size-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              {primary_supplier_name || "-"}
            </span>
          </div>
          <Separator className="my-2" />
          <div className="flex items-center justify-between">
            {/* SKU Code */}
            <div className="flex items-center gap-2 text-sm">
              <Barcode className="size-4 text-muted-foreground" />
              <span className="text-muted-foreground">{sku_id || "-"}</span>
            </div>

            {/* Price */}
            <span className="font-medium text-primary">
              {currency_id || "-"} {price || "-"}
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
