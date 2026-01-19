import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { SupplierProductDetail } from "@/types/supplier";
import Image from "next/image";
import Link from "next/link";

interface ProductPricingCardProps {
  readonly product: SupplierProductDetail;
}

export default function ProductPricingCard({
  product,
}: ProductPricingCardProps) {
  const { name, category, price, currency, image_url } = product || {};
  return (
    <Link href={`/products/${product?.id}/view`}>
      <Card className="hover:shadow-md transition-shadow p-4 flex flex-row gap-4 min-h-full items-center">
        {/* Left side - Image */}
        <div className="relative size-16 shrink-0 rounded-lg overflow-hidden bg-muted">
          <Image
            src={image_url || "/images/danadairy.png"}
            alt={name}
            fill
            sizes="80px"
            loading="eager"
            className="object-cover"
          />
        </div>
        {/* Product Info */}
        <div className="flex-1 min-w-0">
          <Badge variant="secondary" className="mb-2">
            {category || "-"}
          </Badge>
          <h3 className="font-semibold text-sm text-foreground mb-0.5">
            {name || "-"}
          </h3>
          {/* {code && <p className="text-xs text-muted-foreground">{code}</p>} */}
        </div>

        {/* Right side - Price */}
        <div className="shrink-0 text-center">
          <p className="text-xs text-muted-foreground mb-0.5">Price</p>
          <p className="text-sm font-semibold text-primary">
            {currency || "-"} {price || "-"}
          </p>
        </div>
      </Card>
    </Link>
  );
}
