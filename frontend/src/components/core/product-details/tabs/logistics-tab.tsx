import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Product } from "@/types/product";
import { Box, Layers, Thermometer, Truck } from "lucide-react";
import { InfoItem } from "@/components/core/info-item";

interface LogisticsTabProps {
  readonly productDetails?: Product | null;
  readonly mode: "view" | "edit";
}

export default function LogisticsTab({
  productDetails,
  mode,
}: LogisticsTabProps) {
  const isEdit = mode === "edit";
  const {
    cartons_per_pallet,
    loading_quantities,
    transport_temperature,
    storage_temperature,
    carton_dimensions,
    pallet_dimensions,
    term_of_delivery,
  } = productDetails?.logistics_details || {};
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Logistics Information
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={Layers}
              label="Cartons per Pallet"
              name="cartons_per_pallet"
              editable={isEdit}
              value={cartons_per_pallet || ""}
            />
            <InfoItem
              icon={Truck}
              label="Loading Quantities"
              name="loading_quantities"
              editable={isEdit}
              value={loading_quantities || ""}
            />
            <InfoItem
              icon={Thermometer}
              label="Transport Temperature"
              name="transport_temperature"
              editable={isEdit}
              value={transport_temperature || ""}
            />
          </div>
          <div className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={Thermometer}
              label="Storage Temperature"
              name="storage_temperature"
              editable={isEdit}
              value={storage_temperature || ""}
            />
            <InfoItem
              icon={Box}
              label="Carton Dimensions"
              name="carton_dimensions"
              editable={isEdit}
              value={carton_dimensions || ""}
            />
            <InfoItem
              icon={Box}
              label="Pallet Dimensions"
              name="pallet_dimensions"
              editable={isEdit}
              value={pallet_dimensions || ""}
            />
          </div>
          <div className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={Truck}
              label="Term of Delivery"
              name="term_of_delivery"
              editable={isEdit}
              value={term_of_delivery || ""}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
