import SupplierPricingCard from "@/components/core/product-details/supplier-pricing-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Product } from "@/types/product";
import NoDataFound from "@/components/core/no-data-found";

interface SuppliersPricingTabProps {
  readonly productDetails?: Product | null;
  readonly mode: "view" | "edit";
}

export default function SuppliersPricingTab({
  productDetails,
  mode,
}: SuppliersPricingTabProps) {
  const {
    supplier_details,
    moq_production,
    moq_packaging_matereal,
    lead_time_to_production,
    lead_time_to_print_packing_material,
    lead_time_to_reorder_packing_material,
  } = productDetails || {};
  return (
    <div className="space-y-4">
      {supplier_details && supplier_details?.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {supplier_details?.map((supplier) => (
            <SupplierPricingCard key={supplier?.id} supplier={supplier} />
          ))}
        </div>
      ) : (
        <NoDataFound
          title="No suppliers found"
          description="This product has not added any suppliers yet."
        />
      )}
      {/* Production Information Card */}
      <Card>
        <CardHeader>
          <CardTitle>Production Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-6">
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">MOQ - Production</p>
              <p className="text-sm font-medium text-foreground">
                {moq_production || "-"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">MOQ - Packaging</p>
              <p className="text-sm font-medium text-foreground">
                {moq_packaging_matereal || "-"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">
                Lead Time - Production
              </p>
              <p className="text-sm font-medium text-foreground">
                {lead_time_to_production || "-"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Lead Time - Print</p>
              <p className="text-sm font-medium text-foreground">
                {lead_time_to_print_packing_material || "-"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">
                Lead Time - Reorder
              </p>
              <p className="text-sm font-medium text-foreground">
                {lead_time_to_reorder_packing_material || "-"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
