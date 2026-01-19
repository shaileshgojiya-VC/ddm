import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Product } from "@/types/product";
import {
  Barcode,
  Box,
  Building2,
  Clock,
  FileText,
  Globe,
  Layers,
  MapPin,
  Package,
  Tag,
} from "lucide-react";
import { InfoItem } from "@/components/core/info-item";

interface ProductInfoTabProps {
  readonly productDetails?: Product | null;
  readonly mode: "view" | "edit";
  readonly editableFields?: string[];
}

export default function ProductInfoTab({
  productDetails,
  mode,
  editableFields = [],
}: ProductInfoTabProps) {
  const isEdit = mode === "edit";

  const isFieldEditable = (fieldName: string) => {
    return isEdit && editableFields.includes(fieldName);
  };
  const {
    preview_text,
    short_name,
    description,
    category,
    sub_category,
    child_category,
    net_content,
    sku_package,
    package_material,
    specification,
    shelf_life,
    sku_id,
    barcode,
    carton_barcode,
    hs_code,
    art_number,
    unit_pack_size,
    units_per_carton,
    brand_name,
    factory_name,
    country_of_origin,
    origin,
    loading_address,
  } = productDetails || {};
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Basic Information Card */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={FileText}
              label="Preview Text"
              name="preview_text"
              editable={isFieldEditable("preview_text")}
              value={preview_text || "-"}
            />
            <InfoItem
              icon={Tag}
              label="Short Name"
              name="short_name"
              value={short_name || "-"}
              editable={isFieldEditable("short_name")}
            />
            <InfoItem
              icon={FileText}
              label="Description"
              name="description"
              editable={isFieldEditable("description")}
              value={description || "-"}
            />
            <InfoItem
              icon={Layers}
              label="Category"
              name="category"
              editable={isFieldEditable("category")}
              value={category || "-"}
            />
            <InfoItem
              icon={Layers}
              label="Sub Category"
              name="sub_category"
              editable={isFieldEditable("sub_category")}
              value={sub_category || "-"}
            />
            <InfoItem
              icon={Layers}
              label="Child Category"
              name="child_category"
              editable={isFieldEditable("child_category")}
              value={child_category || "-"}
            />
          </CardContent>
        </Card>

        {/* Product Specifications Card */}
        <Card>
          <CardHeader>
            <CardTitle>Product Specifications</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={Package}
              label="Net Content"
              name="net_content"
              editable={isFieldEditable("net_content")}
              value={net_content || "-"}
            />
            <InfoItem
              icon={Box}
              label="SKU Package"
              name="sku_package"
              editable={isFieldEditable("sku_package")}
              value={sku_package || "-"}
            />
            <InfoItem
              icon={Layers}
              label="Package Material"
              name="package_material"
              editable={isFieldEditable("package_material")}
              value={package_material || "-"}
            />
            <InfoItem
              icon={FileText}
              label="Specification"
              name="specification"
              editable={isFieldEditable("specification")}
              value={specification || "-"}
            />
            <InfoItem
              icon={Clock}
              label="Shelf Life"
              name="shelf_life"
              editable={isFieldEditable("shelf_life")}
              value={shelf_life || "-"}
            />
          </CardContent>
        </Card>

        {/* Identifiers Card */}
        <Card>
          <CardHeader>
            <CardTitle>Identifiers</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={Barcode}
              label="SKU"
              name="sku_id"
              editable={isFieldEditable("sku_id")}
              value={sku_id || "-"}
            />
            <InfoItem
              icon={Barcode}
              label="Barcode"
              name="barcode"
              editable={isFieldEditable("barcode")}
              value={barcode || "-"}
            />
            <InfoItem
              icon={Barcode}
              label="Carton Barcode"
              name="carton_barcode"
              editable={isFieldEditable("carton_barcode")}
              value={carton_barcode || "-"}
            />
            <InfoItem
              icon={Tag}
              label="HS Code"
              name="hs_code"
              editable={isFieldEditable("hs_code")}
              value={hs_code || "-"}
            />
            <InfoItem
              icon={Tag}
              label="Art Number"
              name="art_number"
              editable={isFieldEditable("art_number")}
              value={art_number || "-"}
            />
            <InfoItem
              icon={Box}
              label="Unit Pack Size"
              name="unit_pack_size"
              editable={isFieldEditable("unit_pack_size")}
              value={unit_pack_size || "-"}
            />
            <InfoItem
              icon={Package}
              label="Units per Carton"
              name="units_per_carton"
              editable={isFieldEditable("units_per_carton")}
              value={units_per_carton || "-"}
            />
          </CardContent>
        </Card>

        {/* Factory Information Card */}
        <Card>
          <CardHeader>
            <CardTitle>Factory Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={Tag}
              label="Brand"
              name="brand_name"
              editable={isFieldEditable("brand_name")}
              value={brand_name || "-"}
            />
            <InfoItem
              icon={Building2}
              label="Factory"
              name="factory_name"
              editable={isFieldEditable("factory_name")}
              value={factory_name || "-"}
            />
            <InfoItem
              icon={Globe}
              label="Country of Origin"
              name="country_of_origin"
              editable={isFieldEditable("country_of_origin")}
              value={country_of_origin || "-"}
            />
            <InfoItem
              icon={MapPin}
              label="Origin"
              name="origin"
              editable={isFieldEditable("origin")}
              value={origin || "-"}
            />
            <InfoItem
              icon={MapPin}
              label="Loading Address"
              name="loading_address"
              editable={isFieldEditable("loading_address")}
              value={loading_address || "-"}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
