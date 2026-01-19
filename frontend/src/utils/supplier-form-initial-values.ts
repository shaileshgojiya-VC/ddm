import { Supplier, SupplierFormData } from "@/types/supplier";

export function getSupplierFormInitialValues(
  supplier: Supplier
): SupplierFormData {
  const {
    company_name,
    prefix,
    company_type,
    industry,
    address,
    country,
    email,
    phone_number,
    website,
    messanger_number,
    vat_number,
    registraction_number,
    supplier_name,
    buyer_type,
    products_manufactured,
    sub_category,
    child_category,
  } = supplier || {};

  return {
    company_name: company_name || "",
    prefix: prefix || "",
    company_type: company_type || "",
    industry: industry || "",
    address: address || "",
    country: country || "",
    email: email || "",
    phone_number: phone_number || "",
    website: website || "",
    messanger_number: messanger_number || "",
    vat_number: vat_number || "",
    registraction_number: registraction_number || "",
    supplier_name: supplier_name || "",
    buyer_type: buyer_type || "",
    products_manufactured: products_manufactured || "",
    sub_category: sub_category || [],
    child_category: child_category || [],
  };
}
