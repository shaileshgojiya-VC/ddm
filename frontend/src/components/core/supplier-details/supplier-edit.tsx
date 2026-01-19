"use client";
import { updateSupplierAction } from "@/actions/supplier/update-supplier-action";
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
import { Form } from "@/components/ui/form";
import { Supplier, SupplierFormData } from "@/types/supplier";
import { getSupplierFormInitialValues } from "@/utils/supplier-form-initial-values";
import { formatDate } from "@/utils/date-format";
import { Calendar, Loader2, MapPin, Save, SquarePen, User } from "lucide-react";
import Link from "next/link";
import { useTransition } from "react";
import { useForm } from "react-hook-form";

interface SupplierEditProps {
  readonly supplierDetails: Supplier;
  readonly mode: "view" | "edit";
}

export default function SupplierEdit({
  supplierDetails,
  mode,
}: SupplierEditProps) {
  const [isPending, startTransition] = useTransition();
  const { id, company_name, address, last_contact, assigned_by, prefix } =
    supplierDetails || {};

  const form = useForm<SupplierFormData>({
    defaultValues: getSupplierFormInitialValues(supplierDetails),
  });

  const editableFields = Object.keys(form.formState.defaultValues || {});

  const onSubmit = async (data: SupplierFormData) => {
    startTransition(async () => {
      await updateSupplierAction({ id, data });
    });
  };

  const tabs: TabItem[] = [
    {
      value: "supplier-info",
      label: "Supplier Info",
      content: (
        <SupplierInfoTab
          supplierDetails={supplierDetails}
          mode={mode}
          editableFields={editableFields}
        />
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
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        id="supplier-edit-form"
        className="space-y-4"
      >
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
            {mode === "edit" ? (
              <Button
                type="submit"
                form="supplier-edit-form"
                className="shrink-0"
                disabled={!form.formState.isDirty || isPending}
              >
                {isPending ? <Loader2 className="animate-spin" /> : <Save />}
                {isPending ? "Saving..." : "Save Supplier"}
              </Button>
            ) : (
              <Button variant="outline" className="shrink-0" asChild>
                <Link href={`/suppliers/${supplierDetails.id}/edit`}>
                  <SquarePen />
                  Edit Supplier
                </Link>
              </Button>
            )}
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
      </form>
    </Form>
  );
}
