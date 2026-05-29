const BADGE_STYLES: Record<string, string> = {
  "Seminář": "bg-crimson text-white",
  "Konference": "bg-crimson text-white",
  "Kulatý stůl": "bg-navy-purple text-white",
  "Veřejné slyšení": "bg-teal text-white",
  "Tiskové konference": "bg-ink-wash text-ink border border-border-cream",
  "Jednání výborů": "bg-midnight text-white",
};

export function CategoryBadge({ category }: { category: string }) {
  const style = BADGE_STYLES[category] ?? "bg-border-cream text-ink";
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-sans font-medium ${style}`}>
      {category}
    </span>
  );
}
