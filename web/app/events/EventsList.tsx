"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { formatDate, firstThumbnail, type Summary } from "@/lib/types";
import { CategoryBadge } from "../components/CategoryBadge";

export function EventsList({ summaries }: { summaries: Summary[] }) {
  const categories = Array.from(
    new Set(summaries.map((s) => s.event.classification))
  ).sort();

  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const filtered = activeCategory
    ? summaries.filter((s) => s.event.classification === activeCategory)
    : summaries;

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <header className="mb-6">
        <h1 className="font-slab font-bold text-2xl text-navy-9 mb-3">
          Archiv akcí PSP
        </h1>

        {/* Category filter */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setActiveCategory(null)}
            className={`px-3 py-1 rounded text-xs font-sans font-medium transition-colors ${
              activeCategory === null
                ? "bg-navy-9 text-surface-0"
                : "bg-surface-2 text-muted-foreground hover:bg-surface-3"
            }`}
          >
            Vše ({summaries.length})
          </button>
          {categories.map((cat) => {
            const count = summaries.filter(
              (s) => s.event.classification === cat
            ).length;
            return (
              <button
                key={cat}
                onClick={() =>
                  setActiveCategory(activeCategory === cat ? null : cat)
                }
                className={`px-3 py-1 rounded text-xs font-sans font-medium transition-colors ${
                  activeCategory === cat
                    ? "bg-brand-6 text-surface-0"
                    : "bg-surface-2 text-muted-foreground hover:bg-surface-3"
                }`}
              >
                {cat} ({count})
              </button>
            );
          })}
        </div>
      </header>

      <div className="flex flex-col gap-3">
        {filtered.map((s) => {
          const thumb = firstThumbnail(s);
          return (
            <Link
              key={s.event.id}
              href={`/events/${s.event.id}`}
              className="flex gap-3 bg-surface-0 border border-border rounded-lg p-4 hover:border-brand-6 transition-colors group"
            >
              {thumb && (
                <div className="flex-shrink-0 w-24 h-16 rounded overflow-hidden bg-surface-3">
                  <Image
                    src={thumb}
                    alt=""
                    width={96}
                    height={64}
                    className="w-full h-full object-cover"
                    unoptimized
                  />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-1.5">
                  <span className="font-sans text-sm text-muted-foreground">
                    {formatDate(s.event.start_date)}
                  </span>
                  <CategoryBadge category={s.event.classification} />
                </div>
                <h2 className="font-slab font-semibold text-navy-9 group-hover:text-brand-6 transition-colors leading-snug mb-1">
                  {s.event.name}
                </h2>
                <p className="font-sans text-sm text-muted-foreground line-clamp-2 leading-relaxed">
                  {s.summary.topic.split("\n")[0]}
                </p>
                {s.entities.speakers.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {s.entities.speakers.slice(0, 4).map((sp, i) => (
                      <span
                        key={i}
                        className="font-sans text-xs bg-surface-2 text-muted-foreground px-2 py-0.5 rounded"
                      >
                        {sp.name}
                      </span>
                    ))}
                    {s.entities.speakers.length > 4 && (
                      <span className="font-sans text-xs text-muted-foreground">
                        +{s.entities.speakers.length - 4}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
