import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { Supplier } from "@/types/supplier";
import { formatDate } from "@/utils/date-format";
import { Building2, Calendar, Mail, MapPin, Package } from "lucide-react";
import Link from "next/link";

interface SupplierCardProps {
  readonly supplier: Supplier;
}

export default function SupplierCard({ supplier }: SupplierCardProps) {
  const {
    id,
    company_name,
    company_type,
    country,
    email,
    category,
    last_contact = "-",
  } = supplier;
  return (
    <Link href={`/suppliers/${id}/view`}>
      <Card className="hover:shadow-md transition-shadow py-0">
        <CardContent className="p-6 space-y-2">
          {/* Header with Icon and Rating */}
          <div className="flex items-start justify-between">
            <div className="flex items-center justify-center size-12 rounded-lg bg-primary/10">
              <Building2 className="size-6 text-primary" />
            </div>
          </div>

          {/* Company Name */}
          <div className="space-y-2">
            <h3 className="font-semibold text-lg text-foreground">
              {company_name || "-"}
            </h3>
            <Badge variant="secondary">{company_type || "-"}</Badge>
          </div>

          {/* Location */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <MapPin className="size-4 shrink-0" />
            <span>{country || "-"}</span>
          </div>

          {/* Products/Categories */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Package className="size-4 shrink-0" />
            <span className="truncate">
              {category?.length > 0 ? category?.join(", ") : "-"}
            </span>
          </div>

          {/* Email */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Mail className="size-4 shrink-0" />
            <span className="truncate">{email || "-"}</span>
          </div>

          {/* Last Contact */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Calendar className="size-4 shrink-0" />
            <span>{last_contact ? formatDate(last_contact) : "-"}</span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
