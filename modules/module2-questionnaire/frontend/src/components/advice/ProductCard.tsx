import type { RecommendedProduct } from "@/lib/types";

interface ProductCardProps {
  product: RecommendedProduct;
}

export function ProductCard({ product }: ProductCardProps) {
  const confidenceDots = Math.round(product.confidence * 5);

  return (
    <div
      style={{
        backgroundColor: "var(--color-bg-elevated)",
        borderRadius: "var(--radius-lg)",
        overflow: "hidden",
        boxShadow: "var(--shadow-card)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Product image */}
      <div
        style={{
          width: "100%",
          height: "180px",
          backgroundColor: "var(--color-btn-filter)",
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
        }}
      >
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name}
            loading="lazy"
            style={{
              position: "absolute",
              inset: 0,
              width: "100%",
              height: "100%",
              objectFit: "contain",
              padding: "16px",
            }}
          />
        ) : (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <div
              style={{
                width: "48px",
                height: "48px",
                borderRadius: "var(--radius-md)",
                backgroundColor: "var(--color-border)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <span
                style={{
                  fontFamily: "var(--font-sans)",
                  fontSize: "11px",
                  fontWeight: 600,
                  color: "var(--color-fg-subtle)",
                  letterSpacing: "0.5px",
                }}
              >
                {product.sku}
              </span>
            </div>
            <span
              style={{
                fontFamily: "var(--font-sans)",
                fontSize: "11px",
                color: "var(--color-fg-subtle)",
              }}
            >
              無圖片
            </span>
          </div>
        )}
      </div>

      {/* Card body */}
      <div style={{ padding: "20px", flex: 1, display: "flex", flexDirection: "column" }}>
        <p
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "11px",
            fontWeight: 500,
            color: "var(--color-fg-subtle)",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
            marginBottom: "4px",
          }}
        >
          {product.sku}
        </p>
        <h3
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "17px",
            fontWeight: 600,
            color: "var(--color-fg)",
            marginBottom: "8px",
            letterSpacing: "-0.374px",
          }}
        >
          {product.name}
        </h3>
        <p
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: "14px",
            fontWeight: 400,
            color: "var(--color-fg-muted)",
            lineHeight: 1.5,
            flex: 1,
            marginBottom: "16px",
          }}
        >
          {product.reason}
        </p>

        {/* Confidence indicator */}
        <div>
          <p
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "12px",
              fontWeight: 500,
              color: "var(--color-fg-subtle)",
              marginBottom: "6px",
            }}
          >
            符合度 {Math.round(product.confidence * 100)}%
          </p>
          <div style={{ display: "flex", gap: "4px" }}>
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                style={{
                  width: "24px",
                  height: "6px",
                  borderRadius: "var(--radius-pill)",
                  backgroundColor:
                    i < confidenceDots
                      ? "var(--color-accent)"
                      : "var(--color-border)",
                  transition: `background-color var(--duration-fast) ease`,
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
