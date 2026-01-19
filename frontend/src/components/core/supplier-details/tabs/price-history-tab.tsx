import NoDataFound from "@/components/core/no-data-found";
import PriceHistoryItem from "@/components/core/products/price-history-item";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Supplier, SupplierPriceHistory } from "@/types/supplier";

interface PriceHistoryTabProps {
  readonly supplierDetails: Supplier;
}

export default function PriceHistoryTab({
  supplierDetails,
}: PriceHistoryTabProps) {
  // const { price_history_details } = supplierDetails || {};
  const price_history_details: SupplierPriceHistory[] = [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Price History</CardTitle>
        <p className="text-sm text-muted-foreground">
          Historical pricing changes from this supplier
        </p>
      </CardHeader>
      <CardContent className="space-y-3">
        {price_history_details?.length > 0 ? (
          <>
            {price_history_details?.map((history) => (
              <PriceHistoryItem key={history.id} history={history} />
            ))}
          </>
        ) : (
          <NoDataFound
            title="No price history found"
            description="This supplier has not added any price history yet."
          />
        )}
      </CardContent>
    </Card>
  );
}
