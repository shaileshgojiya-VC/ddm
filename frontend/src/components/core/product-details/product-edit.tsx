"use client";
import { updateProductAction } from "@/actions/product/update-product-action";
import BackButton from "@/components/core/back-button";
import CommonTabs, { TabItem } from "@/components/core/common-tabs";
import ProductImages from "@/components/core/product-details/product-images";
import ProductInfoCards from "@/components/core/product-details/product-info-cards";
import ArtworkFilesTab from "@/components/core/product-details/tabs/artwork-files-tab";
import LogisticsTab from "@/components/core/product-details/tabs/logistics-tab";
import OtherInfoTab from "@/components/core/product-details/tabs/other-info-tab";
import PackagingTab from "@/components/core/product-details/tabs/packaging-tab";
import ProductDocumentsTab from "@/components/core/product-details/tabs/product-documents-tab";
import ProductInfoTab from "@/components/core/product-details/tabs/product-info-tab";
import SuppliersPricingTab from "@/components/core/product-details/tabs/suppliers-pricing-tab";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";
import { Product, ProductFormData } from "@/types/product";
import { getProductFormInitialValues } from "@/utils/product-form-initial-values";
import { Loader2, Save, SquarePen } from "lucide-react";
import Link from "next/link";
import { useTransition } from "react";
import { useForm } from "react-hook-form";

interface ProductInfoProps {
  readonly productDetails: Product;
  readonly mode: "view" | "edit";
}
export default function ProductInfo({
  productDetails,
  mode,
}: ProductInfoProps) {
  const [isPending, startTransition] = useTransition();
  const { id, category, name, description } = productDetails || {};

  const form = useForm<ProductFormData>({
    defaultValues: getProductFormInitialValues(productDetails),
  });

  const editableFields = Object.keys(form.formState.defaultValues || {});

  const onSubmit = async (data: ProductFormData) => {
    startTransition(async () => {
      await updateProductAction({ id, data });
    });
  };
  const tabs: TabItem[] = [
    {
      value: "product-info",
      label: "Product Info",
      content: <ProductInfoTab mode={mode} editableFields={editableFields} />,
    },
    {
      value: "suppliers-pricing",
      label: "Suppliers & Pricing",
      content: (
        <SuppliersPricingTab productDetails={productDetails} mode={mode} />
      ),
    },
    {
      value: "logistics",
      label: "Logistics",
      content: <LogisticsTab mode={mode} />,
    },
    {
      value: "packaging",
      label: "Packaging",
      content: <PackagingTab mode={mode} />,
    },
    {
      value: "artwork-files",
      label: "Artwork Files",
      content: <ArtworkFilesTab productDetails={productDetails} mode={mode} />,
    },
    {
      value: "documents",
      label: "Documents",
      content: (
        <ProductDocumentsTab productDetails={productDetails} mode={mode} />
      ),
    },
    {
      value: "other-info",
      label: "Other Info",
      content: <OtherInfoTab mode={mode} />,
    },
  ];
  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        id="product-edit-form"
        className="space-y-4"
      >
        <div className="space-y-6">
          <div className="flex flex-wrap gap-4 items-center justify-between">
            <div className="flex items-start gap-3 flex-1">
              <BackButton />
              <div className="space-y-1 capitalize">
                <Badge variant="secondary">{category || "-"}</Badge>
                <h1 className="text-2xl font-bold tracking-tight ">
                  {name || "-"}
                </h1>
                <p className="text-sm text-muted-foreground flex items-center gap-2">
                  {description || "-"}
                </p>
              </div>
            </div>
            {mode === "edit" ? (
              <Button
                type="submit"
                form="product-edit-form"
                className="shrink-0"
                disabled={!form.formState.isDirty || isPending}
              >
                {isPending ? <Loader2 className="animate-spin" /> : <Save />}
                {isPending ? "Saving..." : "Save Product"}
              </Button>
            ) : (
              <Button variant="outline" className="shrink-0" asChild>
                <Link href={`/products/${productDetails.id}/edit`}>
                  <SquarePen />
                  Edit Product
                </Link>
              </Button>
            )}
          </div>
          {/* Product Images */}
          <ProductImages productDetails={productDetails} />

          {/* Product Info Cards */}
          <ProductInfoCards productDetails={productDetails} />

          {/* Product Info Tabs */}
          <CommonTabs tabs={tabs} defaultValue="product-info" />
        </div>
      </form>
    </Form>
  );
}
