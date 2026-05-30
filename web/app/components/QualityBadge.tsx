const STYLE = {
  good:    { label: "přepis: dobrý",     cls: "text-teal-6 border-teal-6" },
  partial: { label: "přepis: částečný",  cls: "text-orange-6 border-orange-6" },
  poor:    { label: "přepis: slabý",     cls: "text-brand-6 border-brand-6" },
};

export function QualityBadge({ quality }: { quality: "good" | "partial" | "poor" }) {
  const { label, cls } = STYLE[quality];
  return (
    <span className={`inline-block px-2 py-0.5 border rounded-badge text-xs font-sans ${cls}`}>
      {label}
    </span>
  );
}
