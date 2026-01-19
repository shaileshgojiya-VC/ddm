import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { SupplierDetail } from "@/types/product";
import { Building2, ExternalLink } from "lucide-react";
import Link from "next/link";

interface SupplierPricingCardProps {
  readonly supplier: SupplierDetail;
}

export default function SupplierPricingCard({
  supplier,
}: SupplierPricingCardProps) {
  const { id, supplier_name, country_of_origin, price, currency, lead_times } =
    supplier;
  return (
    <Card className="relative overflow-hidden transition-all hover:shadow-md gap-2">
      <CardHeader>
        <div className="flex  items-center gap-3 truncate">
          <Building2 className="size-5" />
          <h3 className="font-semibold text-foreground truncate">
            {supplier_name || "-"}
          </h3>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Selling Price Section */}
        <div className="p-4 bg-muted/50 rounded-lg flex flex-col">
          <p className="text-xs text-muted-foreground mb-1">Selling Price</p>
          <span className="text-2xl font-bold text-primary dark:text-primary">
            {currency || "-"} {price || "-"}
          </span>
          <span className="text-sm text-muted-foreground">per unit</span>
        </div>

        {/* Details Grid */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Country</span>
            <span className="text-sm font-medium text-foreground text-right">
              {country_of_origin || "-"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Lead Time</span>
            <span className="text-sm font-medium text-foreground text-right">
              {lead_times || "-"}
            </span>
          </div>
        </div>

        {/* View Details Button */}
        <Button
          variant="outline"
          className="w-full hover:bg-primary hover:text-primary-foreground"
          asChild
          size="sm"
        >
          <Link href={`/suppliers/${id}/view`}>
            <ExternalLink className="size-4 mr-2" />
            View Supplier Details
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}
