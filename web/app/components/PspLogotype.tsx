const SIZE: Record<string, string> = {
  sm: "text-base",
  md: "text-2xl",
  lg: "text-4xl",
};

interface Props {
  size?: "sm" | "md" | "lg";
}

export function PspLogotype({ size = "md" }: Props) {
  return (
    <span className={`font-bold tracking-tight leading-none ${SIZE[size]}`}>
      <span className="text-brand-6">PSP</span>
      <span className="text-yellow-7">.</span>
      <span className="text-navy-9">VideoArchiv</span>
      <span className="text-yellow-7">.</span>
      <span className="text-navy-9">cz</span>
    </span>
  );
}
