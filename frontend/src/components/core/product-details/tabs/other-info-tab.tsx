import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Product } from "@/types/product";
import { Calendar, Tag, User } from "lucide-react";
import { InfoItem } from "@/components/core/info-item";

interface OtherInfoTabProps {
  readonly productDetails?: Product | null;
  readonly mode: "view" | "edit";
}

export default function OtherInfoTab({
  productDetails,
  mode,
}: OtherInfoTabProps) {
  const isEdit = mode === "edit";
  const {
    active_from,
    active_to,
    external_id,
    created_by,
    created_at,
    updated_by,
    updated_at,
  } = productDetails || {};
  return (
    <Card>
      <CardHeader>
        <CardTitle>Other Information</CardTitle>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Column 1 */}
          <div className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={Calendar}
              label="Active From"
              name="active_from"
              editable={false}
              value={active_from || ""}
            />
            <InfoItem
              icon={Calendar}
              label="Active Until"
              name="active_to"
              editable={false}
              value={active_to || ""}
            />
          </div>

          {/* Column 2 */}
          <div className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={Tag}
              label="External ID"
              name="external_id"
              editable={false}
              value={external_id || ""}
            />
            <InfoItem
              icon={User}
              label="Created By"
              name="created_by"
              editable={false}
              value={created_by || ""}
            />
            <InfoItem
              icon={Calendar}
              label="Created On"
              name="created_at"
              editable={false}
              value={created_at || ""}
            />
          </div>

          {/* Column 3 */}
          <div className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={User}
              label="Modified By"
              name="updated_by"
              editable={false}
              value={updated_by || ""}
            />
            <InfoItem
              icon={Calendar}
              label="Modified On"
              name="updated_at"
              editable={false}
              value={updated_at || ""}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
