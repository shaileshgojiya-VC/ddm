"use client";

import { useProductStore } from "@/stores/use-product-store";
import type { Product } from "@/types/product";
import { useEffect } from "react";

interface ProductStoreInitializerProps {
  product: Product;
  isEditMode?: boolean;
}

export function ProductStoreInitializer({
  product,
  isEditMode = false,
}: ProductStoreInitializerProps) {
  const setCurrentProduct = useProductStore((state) => state.setCurrentProduct);
  const setEditMode = useProductStore((state) => state.setEditMode);

  useEffect(() => {
    if (product) {
      setCurrentProduct(product);
    }
    setEditMode(isEditMode);
  }, [product, isEditMode, setCurrentProduct, setEditMode]);

  return null;
}
