import { create } from "zustand";
import type { Product } from "@/types/product";

interface ProductState {
  currentProduct: Product | null;
  isEditMode: boolean;
  setCurrentProduct: (product: Product) => void;
  clearCurrentProduct: () => void;
  setEditMode: (isEditMode: boolean) => void;
  toggleEditMode: () => void;
}

export const useProductStore = create<ProductState>((set) => ({
  currentProduct: null,
  isEditMode: false,
  setCurrentProduct: (product) => set({ currentProduct: product }),
  clearCurrentProduct: () => set({ currentProduct: null, isEditMode: false }),
  setEditMode: (isEditMode) => set({ isEditMode }),
  toggleEditMode: () => set((state) => ({ isEditMode: !state.isEditMode })),
}));
