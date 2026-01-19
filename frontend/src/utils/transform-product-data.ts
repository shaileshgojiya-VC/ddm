import { Product } from "@/types/product";

/**
 * Transforms product data by replacing null values with a fallback value
 * This prevents React form control errors when null values are passed to inputs
 *
 * @param productData - The product object that may contain null values
 * @param fallbackValue - The value to replace null with (default: "-")
 * @returns Transformed product object with null values replaced
 */
export function transformProductForForm(
  productData: Product,
  fallbackValue: string = "-"
): Product {
  if (!productData || typeof productData !== "object") {
    return productData;
  }

  const transformed: Record<string, unknown> = { ...productData };

  // Recursively process the object
  Object.keys(transformed).forEach((key) => {
    const value = transformed[key];

    // Replace null with fallback value
    if (value === null) {
      transformed[key] = fallbackValue;
    }
    // Recursively handle nested objects (but not arrays)
    else if (
      typeof value === "object" &&
      value !== null &&
      !Array.isArray(value)
    ) {
      transformed[key] = transformProductForForm(
        value as unknown as Product,
        fallbackValue
      );
    }
    // Handle arrays of objects
    else if (Array.isArray(value)) {
      transformed[key] = value.map((item) =>
        typeof item === "object" && item !== null
          ? transformProductForForm(item as unknown as Product, fallbackValue)
          : item === null
          ? fallbackValue
          : item
      );
    }
  });

  return transformed as unknown as Product;
}

/**
 * Transforms product data by replacing null values with empty strings
 * Useful for form inputs that should be empty instead of showing "-"
 *
 * @param productData - The product object that may contain null values
 * @returns Transformed product object with null values replaced with empty strings
 */
export function transformProductForFormWithEmptyStrings(
  productData: Product
): Product {
  return transformProductForForm(productData, "");
}
