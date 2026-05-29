const BADGE_STYLES: Record<string, string> = {
  "Seminář":            "bg-brand-6 text-surface-0",
  "Konference":         "bg-brand-6 text-surface-0",
  "Kulatý stůl":        "bg-navy-6 text-surface-0",
  "Veřejné slyšení":    "bg-teal-6 text-surface-0",
  "Tiskové konference": "bg-surface-2 text-foreground border border-border",
  "Jednání výborů":     "bg-royal-8 text-surface-0",
};

export function CategoryBadge({ category }: { category: string }) {
  const style = BADGE_STYLES[category] ?? "bg-surface-6 text-foreground";
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-sans font-medium ${style}`}>
      {category}
    </span>
  );
}
