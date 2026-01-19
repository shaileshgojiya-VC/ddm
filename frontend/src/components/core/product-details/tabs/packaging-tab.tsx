import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Barcode, Box, Layers, Package } from "lucide-react";
import { Product } from "@/types/product";
import { InfoItem } from "@/components/core/info-item";

interface PackagingTabProps {
  readonly productDetails?: Product | null;
  readonly mode: "view" | "edit";
}

export default function PackagingTab({
  productDetails,
  mode,
}: PackagingTabProps) {
  const isEdit = mode === "edit";
  const {
    net_content,
    sku_package,
    package_material,
    units_per_carton,
    unit_pack_size,
    carton_barcode,
    carton_dimensions,
    cartons_per_pallet,
    pallet_dimensions,
  } = productDetails || {};
  return (
    <Card>
      <CardHeader>
        <CardTitle>Packaging Details</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={Package}
              label="Net Content"
              name="net_content"
              editable={isEdit}
              value={net_content || ""}
            />
            <InfoItem
              icon={Box}
              label="SKU Package"
              name="sku_package"
              editable={isEdit}
              value={sku_package || ""}
            />
            <InfoItem
              icon={Layers}
              label="Package Material"
              name="package_material"
              editable={isEdit}
              value={package_material || ""}
            />
          </div>
          <div className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={Package}
              label="Units per Carton"
              name="units_per_carton"
              editable={isEdit}
              value={units_per_carton || ""}
            />
            <InfoItem
              icon={Box}
              label="Unit Pack Size"
              name="unit_pack_size"
              editable={isEdit}
              value={unit_pack_size || ""}
            />
            <InfoItem
              icon={Barcode}
              label="Carton Barcode"
              name="carton_barcode"
              editable={isEdit}
              value={carton_barcode || ""}
            />
          </div>
          <div className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={Box}
              label="Carton Dimensions"
              name="carton_dimensions"
              editable={isEdit}
              value={carton_dimensions || ""}
            />
            <InfoItem
              icon={Layers}
              label="Cartons per Pallet"
              name="cartons_per_pallet"
              editable={isEdit}
              value={cartons_per_pallet || ""}
            />
            <InfoItem
              icon={Box}
              label="Pallet Dimensions"
              name="pallet_dimensions"
              editable={isEdit}
              value={pallet_dimensions || ""}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
