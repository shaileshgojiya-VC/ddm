"use client";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ChevronRight, Package } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
} from "@/components/ui/sidebar";
import type {
  ProductCategoriesResponse,
  ProductCategory,
} from "@/types/product-category";

interface ProductCategorySidebarProps {
  readonly categoriesData: ProductCategoriesResponse;
}

// Helper function to determine category type based on parent_id and subcategory_id
function getCategoryType(
  category: ProductCategory
): "parent_categories" | "sub_categories" | "child_categories" {
  if (category.parent_id === null && category.subcategory_id === null) {
    return "parent_categories";
  } else if (category.parent_id !== null && category.subcategory_id === null) {
    return "sub_categories";
  } else {
    return "child_categories";
  }
}

export default function ProductCategorySidebar({
  categoriesData,
}: ProductCategorySidebarProps) {
  const { items: categories, total_product_count: totalProductCount } =
    categoriesData;
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const hasActiveFilters =
    searchParams.has("category") ||
    searchParams.has("sub_category") ||
    searchParams.has("child_category");

  const handleClearFilters = () => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("category");
    params.delete("sub_category");
    params.delete("child_category");
    params.set("page", "1");
    router.push(`${pathname}?${params.toString()}`, { scroll: false });
  };

  const handleCategoryClick = (item: ProductCategory) => {
    const params = new URLSearchParams(searchParams.toString());

    // Get category type dynamically
    const categoryType = getCategoryType(item);

    // Category type mapping
    const categoryMap = {
      parent_categories: "category",
      sub_categories: "sub_category",
      child_categories: "child_category",
    } as const;

    const paramName = categoryMap[categoryType];

    // Clear child filters when selecting parent categories
    if (categoryType === "parent_categories") {
      params.delete("sub_category");
      params.delete("child_category");
    } else if (categoryType === "sub_categories") {
      params.delete("child_category");
      params.set("category", item.parent_id ?? "");
    } else if (categoryType === "child_categories") {
      params.set("category", item.parent_id ?? "");
      params.set("sub_category", item.subcategory_id ?? "");
    }
    params.set(paramName, item.id);
    params.set("page", "1");
    router.push(`${pathname}?${params.toString()}`, { scroll: false });
  };

  const renderCategory = (item: ProductCategory) => {
    const hasChildren = item.child_categories?.length > 0;

    // Check if this category is currently active
    const isActive =
      item.id === searchParams.get("category") ||
      item.id === searchParams.get("sub_category") ||
      item.id === searchParams.get("child_category");

    const categoryButton = (
      <SidebarMenuButton
        tooltip={item.name}
        className={cn(
          "h-8 text-xs text-foreground",
          isActive &&
            "bg-primary/10 text-primary hover:bg-primary/20 hover:text-primary data-[state=open]:hover:bg-primary/20 data-[state=open]:hover:text-primary"
        )}
        onClick={() => handleCategoryClick(item)}
      >
        {hasChildren && (
          <ChevronRight className="transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
        )}
        <span className="truncate">{item.name}</span>
        <span className="ml-auto">{item.product_count}</span>
      </SidebarMenuButton>
    );

    if (hasChildren) {
      return (
        <Collapsible key={item.id} asChild className="group/collapsible">
          <SidebarMenuItem>
            <CollapsibleTrigger asChild>{categoryButton}</CollapsibleTrigger>
            <CollapsibleContent>
              <SidebarMenuSub className="pr-0 mr-0">
                {item.child_categories.map(renderCategory)}
              </SidebarMenuSub>
            </CollapsibleContent>
          </SidebarMenuItem>
        </Collapsible>
      );
    }

    return (
      <SidebarMenuItem key={item.id}>
        <SidebarMenuSubButton
          className={cn(
            "h-8 text-xs cursor-pointer text-foreground",
            isActive &&
              "bg-primary/10 text-primary hover:bg-primary/20 hover:text-primary"
          )}
          onClick={() => handleCategoryClick(item)}
        >
          <span className="flex items-center justify-between w-full">
            <span className="truncate">{item.name}</span>
            <span>{item.product_count}</span>
          </span>
        </SidebarMenuSubButton>
      </SidebarMenuItem>
    );
  };

  if (!categories?.length) {
    return (
      <div className="lg:w-72 w-full shrink-0 lg:sticky top-0 h-fit z-10">
        <div className="rounded-lg border bg-card">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <h3 className="font-semibold">Categories</h3>
          </div>
        </div>
      </div>
    );
  }

  const isAllProductsActive = !hasActiveFilters;

  return (
    <div className="lg:w-[280px] w-full shrink-0 lg:sticky top-0 max-h-fit z-10">
      <div className="rounded-lg border bg-card">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h3 className="font-semibold">Categories</h3>
          {hasActiveFilters && (
            <Button
              variant="secondary"
              size="sm"
              onClick={handleClearFilters}
              className="h-auto p-0 text-xs text-primary bg-transparent hover:bg-transparent"
            >
              Clear
            </Button>
          )}
        </div>

        {/* All Products Button */}
        <div className="p-2">
          <button
            onClick={handleClearFilters}
            className={cn(
              "flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors hover:bg-accent",
              isAllProductsActive &&
                "bg-primary text-primary-foreground hover:bg-primary/90"
            )}
          >
            <Package className="size-4" />
            <span className="flex-1 text-left font-medium">All Products</span>
            <span
              className={cn(
                "text-xs rounded-full bg-muted px-2 py-0.5",
                isAllProductsActive &&
                  "bg-primary-foreground/20 text-primary-foreground"
              )}
            >
              {totalProductCount}
            </span>
          </button>
        </div>

        {/* Categories List */}
        <SidebarMenu className="max-h-[calc(100vh-200px)] overflow-hidden overflow-y-auto p-2">
          {categories.map(renderCategory)}
        </SidebarMenu>
      </div>
    </div>
  );
}
