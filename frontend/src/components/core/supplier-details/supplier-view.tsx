import BackButton from "@/components/core/back-button";
import CommonTabs, { type TabItem } from "@/components/core/common-tabs";
import InfoItemCard from "@/components/core/info-item-card";
import DocumentsTab from "@/components/core/supplier-details/tabs/documents-tab";
import EmailCommunicationsTab from "@/components/core/supplier-details/tabs/email-communications-tab";
import PriceHistoryTab from "@/components/core/supplier-details/tabs/price-history-tab";
import ProductsPricingTab from "@/components/core/supplier-details/tabs/products-pricing-tab";
import SupplierInfoTab from "@/components/core/supplier-details/tabs/supplier-info-tab";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Supplier } from "@/types/supplier";
import { formatDate } from "@/utils/date-format";
import { Calendar, MapPin, SquarePen, User } from "lucide-react";
import Link from "next/link";

interface SupplierViewProps {
  readonly supplierDetails: Supplier;
  readonly mode: "view" | "edit";
}

export default function SupplierView({
  supplierDetails,
  mode = "view",
}: SupplierViewProps) {
  const { id, company_name, address, last_contact, assigned_by, prefix } =
    supplierDetails || {};

  const tabs: TabItem[] = [
    {
      value: "supplier-info",
      label: "Supplier Info",
      content: (
        <SupplierInfoTab supplierDetails={supplierDetails} mode={mode} />
      ),
    },
    {
      value: "products-pricing",
      label: "Products & Pricing",
      content: <ProductsPricingTab supplierDetails={supplierDetails} />,
    },
    {
      value: "price-history",
      label: "Price History",
      content: <PriceHistoryTab supplierDetails={supplierDetails} />,
    },
    {
      value: "email-communications",
      label: "Email Communications",
      content: <EmailCommunicationsTab supplierDetails={supplierDetails} />,
    },
    {
      value: "documents",
      label: "Documents",
      content: <DocumentsTab supplierDetails={supplierDetails} />,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-start gap-3">
          <BackButton />
          <div className="space-y-1 capitalize">
            <div className="flex gap-2">
              <Badge variant="secondary">{company_name || "-"}</Badge>
              <Badge variant="outline">{prefix || "-"}</Badge>
            </div>
            <h1 className="text-2xl font-bold tracking-tight ">
              {company_name || "-"}
            </h1>
            <p className="text-sm text-muted-foreground flex items-center gap-2">
              <MapPin className="size-4 shrink-0" />
              {address || "-"}
            </p>
          </div>
        </div>
        {/* <Button variant="outline" className="shrink-0" asChild>
          <Link href={`/suppliers/${id}/edit`}>
            <SquarePen />
            Edit Supplier
          </Link>
        </Button> */}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        <InfoItemCard
          icon={User}
          label="Responsible"
          value={assigned_by || "-"}
        />
        <InfoItemCard
          icon={Calendar}
          label="Last Contact"
          value={last_contact ? formatDate(last_contact) : "-"}
        />
      </div>
      <CommonTabs tabs={tabs} defaultValue="supplier-info" />
    </div>
  );
}
