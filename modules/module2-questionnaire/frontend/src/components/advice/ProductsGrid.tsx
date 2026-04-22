import type { RecommendedProduct } from "@/lib/types";
import { ProductCard } from "./ProductCard";

interface ProductsGridProps {
  products: RecommendedProduct[];
}

export function ProductsGrid({ products }: ProductsGridProps) {
  if (products.length === 0) {
    return null;
  }

  return (
    <section>
      <h2
        style={{
          fontFamily: "var(--font-display)",
          fontSize: "22px",
          fontWeight: 600,
          color: "var(--color-fg)",
          marginBottom: "20px",
          letterSpacing: "-0.374px",
        }}
      >
        推薦產品
      </h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: "20px",
        }}
      >
        {products.map((product) => (
          <ProductCard key={product.sku} product={product} />
        ))}
      </div>
    </section>
  );
}
