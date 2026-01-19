import { cn } from "@/lib/utils";
import type { SupplierPriceHistory } from "@/types/supplier";
import { formatDate } from "@/utils/date-format";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface PriceHistoryItemProps {
  readonly history: SupplierPriceHistory;
}

export default function PriceHistoryItem({ history }: PriceHistoryItemProps) {
  const { product_name, effective_from, price, currency } = history;
  const change = -2;
  const getTrendIcon = () => {
    if (change >= 0) {
      return <TrendingUp className="size-5" />;
    }
    if (change < 0) {
      return <TrendingDown className="size-5" />;
    }
    return <Minus className="size-5" />;
  };

  const getTrendColor = () => {
    if (change > 0) {
      return "bg-red-100 text-red-600";
    }
    if (change < 0) {
      return "bg-green-100 text-green-600";
    }
    return "bg-gray-100 text-gray-600";
  };

  const getPercentageColor = () => {
    if (change > 0) {
      return "text-red-600";
    }
    if (change < 0) {
      return "text-green-600";
    }
    return "text-muted-foreground";
  };

  const formatPercentage = () => {
    if (change > 0) {
      return `+${change}%`;
    }
    return `${change}%`;
  };

  return (
    <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
      <div className="flex items-center gap-4">
        {/* Trend Icon */}
        <div
          className={cn(
            "flex items-center justify-center size-10 rounded-full shrink-0",
            getTrendColor()
          )}
        >
          {getTrendIcon()}
        </div>

        {/* Product Info */}
        <div className="flex flex-col gap-1">
          <h4 className="font-semibold  text-foreground">
            {product_name || "-"}
          </h4>
          <p className="text-sm text-muted-foreground">
            {effective_from ? formatDate(effective_from) : "-"}
          </p>
        </div>
      </div>

      {/* Price and Percentage */}
      <div className="flex flex-col items-center gap-1">
        <p className=" font-semibold text-foreground">
          {currency || "-"} {price || "-"}
        </p>
        <p
          className={cn(
            "text-sm font-medium min-w-12 text-right",
            getPercentageColor()
          )}
        >
          {formatPercentage()}
        </p>
      </div>
    </div>
  );
}
