import DataTable, { type Column } from "@/components/core/data-table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Inquiry, ProductDetail } from "@/types/inquiry";
import { formatDate } from "@/utils/date-format";

// Cell renderer components
function ProductNameCell({ product }: { readonly product: ProductDetail }) {
  return (
    <div className="flex items-center gap-2">
      <span>{product?.name || "-"}</span>
    </div>
  );
}

function QuantityCell({ product }: { readonly product: ProductDetail }) {
  return <>{product?.quantity || "-"}</>;
}

function PackagingCell({ product }: { readonly product: ProductDetail }) {
  return <>{product?.package_size || "-"}</>;
}

function TargetPriceCell({ product }: { readonly product: ProductDetail }) {
  return (
    <span className="font-medium">
      {product?.currency_id || "-"} {product?.target_price || "-"}
    </span>
  );
}

function CertificationsCell({ product }: { readonly product: ProductDetail }) {
  return (
    <>
      {product?.certificate?.length > 0 ? (
        <div className="flex items-center gap-1 flex-wrap">
          {product?.certificate?.map((category) => (
            <Badge key={category} variant="outline">
              {category}
            </Badge>
          ))}
        </div>
      ) : (
        "-"
      )}
    </>
  );
}

const columns: Column<ProductDetail>[] = [
  {
    header: "Product Name",
    cell: (product) => <ProductNameCell product={product} />,
  },
  {
    header: "Quantity",
    cell: (product) => <QuantityCell product={product} />,
  },
  {
    header: "Packaging",
    cell: (product) => <PackagingCell product={product} />,
  },
  {
    header: "Target Price",
    cell: (product) => <TargetPriceCell product={product} />,
  },
  {
    header: "Certifications",
    cell: (product) => <CertificationsCell product={product} />,
  },
];

interface OverviewTabProps {
  readonly inquiryDetails: Inquiry;
}

export default function OverviewTab({ inquiryDetails }: OverviewTabProps) {
  const { product_details, etd, destination_country } = inquiryDetails || {};
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Product Requirements{" "}
          {product_details &&
            product_details?.length > 0 &&
            `${product_details?.length} ${
              product_details?.length > 1 ? "SKUs" : "SKU"
            }`}
        </CardTitle>
      </CardHeader>
      <CardContent className="max-h-[500px] overflow-y-auto">
        <DataTable
          data={product_details || []}
          columns={columns}
          getRowKey={(product) => product.id}
        />
        <div className="flex items-center gap-6 mt-4 pt-4 border-t text-sm">
          <div>
            <span className="text-muted-foreground">Destination: </span>
            <span className="font-medium">{destination_country || "-"}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Delivery: </span>
            <span className="font-medium">{etd ? formatDate(etd) : "-"}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
