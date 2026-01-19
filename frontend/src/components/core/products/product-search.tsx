import { SearchInput } from "@/components/core/search-input";
import { Card, CardContent } from "@/components/ui/card";

export default function ProductSearch() {
  return (
    <Card>
      <CardContent className="flex flex-col lg:flex-row items-center gap-4 pt-0">
        <SearchInput
          placeholder="Search products by name, SKU..."
          className="flex-1 w-full lg:w-auto"
        />
      </CardContent>
    </Card>
  );
}
