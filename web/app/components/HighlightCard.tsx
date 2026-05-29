import Image from "next/image";
import type { HighlightItem } from "@/lib/types";
import { formatDate } from "@/lib/types";
import { PspLogotype } from "./PspLogotype";

interface Props {
  highlight: HighlightItem;
  eventName: string;
  category: string;
  date: string;
}

export function HighlightCard({ highlight, eventName, category, date }: Props) {
  return (
    /* Outer wrapper: left crimson strip + newsprint background, shadow for depth */
    <div className="flex rounded-lg overflow-hidden shadow-md bg-surface-1 max-w-xl">
      {/* Left crimson strip */}
      <div className="w-1.5 flex-shrink-0 bg-brand-6" />

      {/* Card body */}
      <div className="flex flex-col flex-1 min-w-0">

        {/* Screenshot */}
        {highlight.screenshot_path?.startsWith("http") && (
          <div className="w-full aspect-[16/9] overflow-hidden bg-surface-3">
            <Image
              src={highlight.screenshot_path}
              alt={`Screenshot — ${highlight.speaker}`}
              width={800}
              height={450}
              className="w-full h-full object-cover"
              unoptimized
            />
          </div>
        )}

        {/* Content */}
        <div className="px-5 pt-4 pb-5 flex flex-col gap-3">
          {/* Category badge */}
          <div>
            <span className="inline-block bg-brand-6 text-surface-0 font-sans font-bold text-[10px] uppercase tracking-widest px-2.5 py-1 rounded-sm">
              {category}
            </span>
          </div>

          {/* Date + event name */}
          <div>
            <p className="font-sans text-xs text-muted-foreground mb-0.5">
              {formatDate(date)}
            </p>
            <p className="font-slab text-sm font-semibold text-navy-9 leading-snug">
              {eventName}
            </p>
          </div>

          {/* Quote */}
          <div className="relative">
            <span
              aria-hidden
              className="absolute -top-2 -left-1 font-slab text-5xl text-brand-6 leading-none select-none"
            >
              &ldquo;
            </span>
            <blockquote className="font-slab text-xl font-bold text-navy-9 leading-tight pl-7 pr-4">
              {highlight.text}
            </blockquote>
          </div>

          {/* Divider */}
          <hr className="border-border" />

          {/* Attribution + logotype */}
          <div className="flex items-end justify-between gap-2">
            <p className="font-sans text-xs leading-relaxed">
              <span className="font-bold text-brand-6 uppercase tracking-wide">
                {highlight.speaker}
              </span>
              {highlight.affiliation && (
                <span className="text-muted-foreground">
                  {", "}
                  {highlight.affiliation}
                </span>
              )}
              {highlight.timestamp && (
                <span className="text-muted-foreground">
                  {" · "}
                  {highlight.timestamp}
                </span>
              )}
            </p>
            <div className="flex-shrink-0">
              <PspLogotype size="xs" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
