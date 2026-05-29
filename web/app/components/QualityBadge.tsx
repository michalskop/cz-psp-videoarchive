const STYLE = {
  good: { label: "přepis: dobrý", cls: "text-teal border-teal" },
  partial: { label: "přepis: částečný", cls: "text-orange border-orange" },
  poor: { label: "přepis: slabý", cls: "text-crimson border-crimson" },
};

export function QualityBadge({ quality }: { quality: "good" | "partial" | "poor" }) {
  const { label, cls } = STYLE[quality];
  return (
    <span className={`inline-block px-2 py-0.5 border rounded text-xs font-sans ${cls}`}>
      {label}
    </span>
  );
}
