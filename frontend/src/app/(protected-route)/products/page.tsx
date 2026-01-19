import { Suspense } from "react";

import PageHeading from "@/components/core/page-heading";
import Pagination from "@/components/core/pagination";
import ProductSearch from "@/components/core/products/product-search";
import ProductCategorySidebar from "@/components/core/products/product-category-sidebar";
import ProductList from "@/components/core/products/product-list";
import ViewToggle from "@/components/core/view-toggle";
import SuspenseLoader from "@/components/core/suspense-loader";
import { ProductsSearchParams } from "@/types/product";
import { ProductCategory } from "@/types/product-category";
import { getCategories, getProducts } from "@/lib/data";
import { Badge } from "@/components/ui/badge";

interface ProductsPageProps {
  readonly searchParams: Promise<ProductsSearchParams>;
}

/**
 * Find category by ID in the API category structure (recursive search)
 */
function findCategoryById(
  categories: ProductCategory[],
  id: string
): ProductCategory | null {
  for (const category of categories) {
    if (category.id === id) {
      return category;
    }
    if (category.child_categories.length > 0) {
      const found = findCategoryById(category.child_categories, id);
      if (found) return found;
    }
  }
  return null;
}

export default async function ProductsPage({
  searchParams,
}: ProductsPageProps) {
  const resolvedSearchParams = await searchParams;
  const categoriesData = await getCategories();
  const { products = [], pagination } = await getProducts(resolvedSearchParams);

  const view = resolvedSearchParams.view || "grid";
  const selectedCategory = resolvedSearchParams.category;
  const selectedSubCategory = resolvedSearchParams.sub_category;
  const selectedChildCategory = resolvedSearchParams.child_category;

  // Get selected category name for display
  const getCategoryBreadcrumb = () => {
    if (!selectedCategory) return null;

    const category = findCategoryById(categoriesData.items, selectedCategory);
    if (!category) return null;

    let breadcrumb = category.name;

    if (selectedSubCategory) {
      const subCategory = findCategoryById(
        categoriesData.items,
        selectedSubCategory
      );
      if (subCategory) {
        breadcrumb += ` → ${subCategory.name}`;

        if (selectedChildCategory) {
          const childCategory = findCategoryById(
            categoriesData.items,
            selectedChildCategory
          );
          if (childCategory) {
            breadcrumb += ` → ${childCategory.name}`;
          }
        }
      }
    }

    return breadcrumb;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <PageHeading
          title="Products"
          description="Dana Dairy product catalog"
        />
        <ViewToggle />
      </div>

      {/* Main Content with Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
        {/* Category Sidebar */}
        <ProductCategorySidebar categoriesData={categoriesData} />

        {/* Products Content */}
        <div className="flex-1 space-y-4 min-w-0">
          {/* Search */}
          <Suspense
            fallback={<SuspenseLoader title="Loading products filters..." />}
          >
            <ProductSearch />
          </Suspense>
          {/* Category Breadcrumb & Count */}
          <div className="flex items-center justify-between">
            <p className="mb-1 text-sm font-medium text-foreground flex items-center gap-2">
              Showing {products?.length} products
              {getCategoryBreadcrumb() && (
                <span>
                  in
                  <Badge variant="secondary" className="ml-1">
                    {getCategoryBreadcrumb()}
                  </Badge>
                </span>
              )}
            </p>
          </div>

          {/* Products Grid/List */}
          <ProductList products={products} view={view} />

          {/* Pagination */}
          <Pagination pagination={pagination} />
        </div>
      </div>
    </div>
  );
}
