import Image from "next/image";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Product } from "@/types/product";

interface ProductImagesProps {
  readonly productDetails: Product;
}

export default function ProductImages({ productDetails }: ProductImagesProps) {
  const { image_urls = [], document_details = [] } = productDetails;

  // Priority 1: Check if image_urls is available and has items
  let images: string[] = [];

  if (image_urls && image_urls.length > 0) {
    images = image_urls;
  }
  // Priority 2: Check document_details for images
  else if (document_details && document_details.length > 0) {
    const imageDocuments = document_details.filter((doc) =>
      doc.file_type?.toLowerCase().includes("image")
    );
    images = imageDocuments.map((doc) => doc.path);
  }

  // Priority 3: Use default images if no images found
  if (images.length === 0) {
    images = ["/images/danadairy.png", "/images/danadairy.png"];
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Product Images</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {images?.length > 0 &&
            images?.map((image, index) => (
              <div
                key={image + index}
                className="relative aspect-square overflow-hidden rounded-lg bg-muted"
              >
                <Image
                  src={image}
                  alt="dana dairy product image"
                  fill
                  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                  loading="eager"
                  className="object-cover"
                />
              </div>
            ))}
        </div>
      </CardContent>
    </Card>
  );
}
