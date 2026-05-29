const SIZE: Record<string, string> = {
  xs:  "text-xs",
  sm:  "text-base",
  md:  "text-2xl",
  lg:  "text-4xl",
};

interface Props {
  size?: "xs" | "sm" | "md" | "lg";
}

/** Universal logotype: snemovna.DataTimes.cz/videoarchiv */
export function PspLogotype({ size = "md" }: Props) {
  return (
    <span className={`font-bold tracking-tight leading-none ${SIZE[size]}`}>
      <span className="text-brand-6">snemovna</span>
      <span className="text-yellow-7">.</span>
      <span className="text-navy-9">DataTimes</span>
      <span className="text-yellow-7">.</span>
      <span className="text-navy-9">cz/videoarchiv</span>
    </span>
  );
}
