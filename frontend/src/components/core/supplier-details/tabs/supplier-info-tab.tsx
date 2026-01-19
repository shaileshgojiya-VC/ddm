import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { InfoItem } from "@/components/core/info-item";
import {
  Building2,
  Hash,
  Factory,
  Building,
  MapPin,
  Globe,
  Mail,
  Phone,
  Globe2,
  MessageSquare,
  FileText,
  Briefcase,
  User,
  Package,
  ShoppingBag,
} from "lucide-react";
import { Supplier } from "@/types/supplier";
import { formatDate } from "@/utils/date-format";
import Link from "next/link";
import { normalizeWebsite } from "@/utils/normalize-website";

interface SupplierInfoTabProps {
  readonly supplierDetails: Supplier;
  readonly mode?: "view" | "edit";
  readonly editableFields?: string[];
}
export default function SupplierInfoTab({
  supplierDetails,
  mode = "view",
  editableFields = [],
}: SupplierInfoTabProps) {
  const isEdit = mode === "edit";

  const isFieldEditable = (fieldName: string) => {
    return isEdit && editableFields.includes(fieldName);
  };
  const {
    company_name,
    prefix,
    address,
    country,
    company_type,
    industry,
    email,
    phone_number,
    website,
    messanger_number,
    vat_number,
    registraction_number,
    supplier_name,
    assigned_by,
    created_on,
    generated_by,
    updated_by,
    buyer_type,
    products_manufactured,
    sub_category,
    child_category,
  } = supplierDetails || {};

  // Merge sub_category and child_category, remove duplicates
  const productCategories = [
    ...(sub_category || []),
    ...(child_category || []),
  ].filter((cat, index, array) => cat && array.indexOf(cat) === index);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Company Information Card */}
        <Card>
          <CardHeader>
            <CardTitle>Company Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={Building2}
              label="Company Name"
              name="company_name"
              editable={isFieldEditable("company_name")}
              value={company_name || "-"}
            />
            <InfoItem
              icon={Hash}
              label="Prefix"
              name="prefix"
              editable={isFieldEditable("prefix")}
              value={prefix || "-"}
            />
            <InfoItem
              icon={Factory}
              label="Company Type"
              name="company_type"
              editable={isFieldEditable("company_type")}
              value={company_type || "-"}
            />
            <InfoItem
              icon={Building}
              label="Industry"
              name="industry"
              editable={isFieldEditable("industry")}
              value={industry || "-"}
            />
            <InfoItem
              icon={MapPin}
              label="Address"
              name="address"
              editable={isFieldEditable("address")}
              value={address || "-"}
            />
            <InfoItem
              icon={Globe}
              label="Country"
              name="country"
              editable={isFieldEditable("country")}
              value={country || "-"}
            />
          </CardContent>
        </Card>

        {/* Contact Details Card */}
        <Card>
          <CardHeader>
            <CardTitle>Contact Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={Mail}
              label="Email"
              name="email"
              editable={isFieldEditable("email")}
              value={
                !isEdit && email ? (
                  <Link
                    href={`mailto:${email}`}
                    target="_blank"
                    className="text-primary"
                  >
                    {email}
                  </Link>
                ) : (
                  email || "-"
                )
              }
            />
            <InfoItem
              icon={Phone}
              label="Phone"
              name="phone_number"
              editable={isFieldEditable("phone_number")}
              value={
                !isEdit && phone_number ? (
                  <Link
                    href={`tel:${phone_number}`}
                    target="_blank"
                    className="text-primary"
                  >
                    {phone_number}
                  </Link>
                ) : (
                  phone_number || "-"
                )
              }
            />
            <InfoItem
              icon={Globe2}
              label="Website"
              name="website"
              editable={isFieldEditable("website")}
              value={
                !isEdit && website
                  ? (() => {
                      const normalizedUrl = normalizeWebsite(website);
                      // Validate URL before using it in Link
                      try {
                        new URL(normalizedUrl);
                        return (
                          <Link
                            href={normalizedUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary"
                          >
                            {website}
                          </Link>
                        );
                      } catch {
                        // If URL is invalid, just display the text
                        return website || "-";
                      }
                    })()
                  : website || "-"
              }
            />
            <InfoItem
              icon={MessageSquare}
              label="Messenger"
              name="messanger_number"
              editable={isFieldEditable("messanger_number")}
              value={messanger_number || "-"}
            />
          </CardContent>
        </Card>

        {/* Business Details Card */}
        <Card>
          <CardHeader>
            <CardTitle>Business Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={FileText}
              label="VAT Number"
              name="vat_number"
              editable={isFieldEditable("vat_number")}
              value={vat_number || "-"}
            />
            <InfoItem
              icon={FileText}
              label="Registration Number"
              name="registraction_number"
              editable={isFieldEditable("registraction_number")}
              value={registraction_number || "-"}
            />
            <InfoItem
              icon={Briefcase}
              label="Supplier Name"
              name="supplier_name"
              editable={isFieldEditable("supplier_name")}
              value={supplier_name || "-"}
            />
            <InfoItem
              icon={User}
              label="Type of Buyer"
              name="buyer_type"
              editable={isFieldEditable("buyer_type")}
              value={buyer_type || "-"}
            />
          </CardContent>
        </Card>

        {/* Product Information Card */}
        <Card>
          <CardHeader>
            <CardTitle>Product Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 divide-y *:pb-3 *:last:pb-0">
            <InfoItem
              icon={Package}
              label="Product Categories"
              name="sub_category"
              editable={
                isFieldEditable("sub_category") ||
                isFieldEditable("child_category")
              }
              value={productCategories?.length > 0 ? productCategories : "-"}
            />
            <InfoItem
              icon={ShoppingBag}
              label="Products Manufactured"
              name="products_manufactured"
              editable={isFieldEditable("products_manufactured")}
              value={products_manufactured || "-"}
            />
          </CardContent>
        </Card>
      </div>

      {/* User Information Card - Full Width */}
      <Card>
        <CardHeader>
          <CardTitle>User Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">
                Responsible Person
              </p>
              <p className="text-sm font-medium text-foreground">
                {assigned_by || "-"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Created By</p>
              <p className="text-sm font-medium text-foreground">
                {generated_by || "-"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Created On</p>
              <p className="text-sm font-medium text-foreground">
                {created_on ? formatDate(created_on) : "-"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Modified By</p>
              <p className="text-sm font-medium text-foreground">
                {updated_by || "-"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
