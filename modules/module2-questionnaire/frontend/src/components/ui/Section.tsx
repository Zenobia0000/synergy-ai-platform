import { HTMLAttributes } from "react";

interface SectionProps extends HTMLAttributes<HTMLElement> {
  title?: string;
  description?: string;
  maxWidth?: number;
}

function Section({ title, description, maxWidth = 640, children, style, ...props }: SectionProps) {
  const sectionStyle: React.CSSProperties = {
    width: "100%",
    maxWidth: `${maxWidth}px`,
    marginLeft: "auto",
    marginRight: "auto",
    paddingLeft: "24px",
    paddingRight: "24px",
    paddingTop: "48px",
    paddingBottom: "48px",
    ...style,
  };

  const titleStyle: React.CSSProperties = {
    fontFamily: "var(--font-display)",
    fontSize: "28px",
    fontWeight: 400,
    lineHeight: 1.14,
    letterSpacing: "0.196px",
    color: "var(--color-fg)",
    margin: "0 0 8px",
  };

  const descStyle: React.CSSProperties = {
    fontFamily: "var(--font-sans)",
    fontSize: "17px",
    fontWeight: 400,
    lineHeight: 1.47,
    letterSpacing: "-0.374px",
    color: "var(--color-fg-muted)",
    margin: "0 0 24px",
  };

  return (
    <section style={sectionStyle} {...props}>
      {title && <h2 style={titleStyle}>{title}</h2>}
      {description && <p style={descStyle}>{description}</p>}
      {children}
    </section>
  );
}

export { Section };
export type { SectionProps };
