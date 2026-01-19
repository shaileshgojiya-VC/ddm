import { Barcode, Clock, DollarSign, Package, Thermometer } from "lucide-react";

import { Product } from "@/types/product";
import InfoItemCard from "@/components/core/info-item-card";

interface ProductInfoCardsProps {
  readonly productDetails: Product;
}

export default function ProductInfoCards({
  productDetails,
}: ProductInfoCardsProps) {
  const { sku_id, storage_conditions, price, net_content, shelf_life } =
    productDetails;
  const infoCards = [
    {
      icon: Barcode,
      label: "SKU",
      value: sku_id || "-",
    },
    {
      icon: DollarSign,
      label: "Selling Price",
      value: price || "-",
    },
    {
      icon: Package,
      label: "Net Content",
      value: net_content || "-",
    },
    {
      icon: Clock,
      label: "Shelf Life",
      value: shelf_life || "-",
    },
    {
      icon: Thermometer,
      label: "Storage",
      value: storage_conditions || "-",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
      {infoCards?.map((card) => {
        return (
          <InfoItemCard
            key={card?.label}
            icon={card?.icon}
            label={card?.label}
            value={card?.value}
          />
        );
      })}
    </div>
  );
}
