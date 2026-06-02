"use client";

import Link from "next/link";
import Image from "next/image";
import { useState, useMemo } from "react";
import { formatDate, firstThumbnail, type Summary } from "@/lib/types";
import { CategoryBadge } from "../components/CategoryBadge";

const CZ_MONTHS = [
  "Leden","Únor","Březen","Duben","Květen","Červen",
  "Červenec","Srpen","Září","Říjen","Listopad","Prosinec",
];

function monthKey(dateStr: string): string {
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function monthLabel(key: string): string {
  const [year, month] = key.split("-");
  return `${CZ_MONTHS[parseInt(month) - 1]} ${year}`;
}

export function EventsList({ summaries }: { summaries: Summary[] }) {
  const categories = useMemo(
    () => Array.from(new Set(summaries.map((s) => s.event.classification))).sort(),
    [summaries]
  );

  // Filter state: 'all' = neutral (no explicit selection), 'filter' = explicit on/off per category
  const [filterMode, setFilterMode] = useState<"all" | "filter">("all");
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());

  const clickCategory = (cat: string) => {
    if (filterMode === "all") {
      // Enter filter mode: only this category is on, all others off
      setFilterMode("filter");
      setSelectedCategories(new Set([cat]));
    } else {
      setSelectedCategories((prev) => {
        const next = new Set(prev);
        if (next.has(cat)) next.delete(cat);
        else next.add(cat);
        return next;
      });
    }
  };

  const clickAll = () => {
    setFilterMode("all");
    setSelectedCategories(new Set());
  };

  // neutral = part of "all" mode; on = explicitly selected; off = explicitly excluded
  const catState = (cat: string): "neutral" | "on" | "off" =>
    filterMode === "all" ? "neutral" : selectedCategories.has(cat) ? "on" : "off";

  const filtered =
    filterMode === "all"
      ? summaries
      : summaries.filter((s) => selectedCategories.has(s.event.classification));

  const groups = useMemo(() => {
    const map = new Map<string, Summary[]>();
    for (const s of filtered) {
      const key = monthKey(s.event.start_date);
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(s);
    }
    return Array.from(map.entries())
      .sort(([a], [b]) => b.localeCompare(a))
      .map(([key, items]) => ({ key, label: monthLabel(key), items }));
  }, [filtered]);

  // Default: two most recent months open
  const defaultOpen = useMemo(() => {
    const keys = Array.from(new Set(summaries.map((s) => monthKey(s.event.start_date))))
      .sort((a, b) => b.localeCompare(a));
    return new Set(keys.slice(0, 2));
  }, [summaries]);

  const [openMonths, setOpenMonths] = useState<Set<string>>(defaultOpen);

  const toggleMonth = (key: string) => {
    setOpenMonths((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <header className="mb-6">
        <h1 className="font-slab font-bold text-2xl text-navy-9 mb-3">
          Archiv akcí PSP
        </h1>

        {/* Category filter: All (neutral mode) | On (explicitly included) | Off (excluded) */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={clickAll}
            className={`px-3 py-1 rounded-badge text-xs font-sans font-medium transition-colors ${
              filterMode === "all"
                ? "bg-navy-9 text-surface-0"
                : "bg-surface-2 text-muted-foreground hover:bg-surface-3"
            }`}
          >
            Vše ({summaries.length})
          </button>
          {categories.map((cat) => {
            const state = catState(cat);
            const count = summaries.filter((s) => s.event.classification === cat).length;
            return (
              <button
                key={cat}
                onClick={() => clickCategory(cat)}
                className={`px-3 py-1 rounded-badge text-xs font-sans font-medium transition-all ${
                  state === "on"
                    ? "bg-brand-6 text-surface-0 border border-brand-6"
                    : state === "off"
                    ? "border border-border text-muted-foreground opacity-40 line-through hover:opacity-60"
                    : "border border-border bg-surface-0 text-foreground hover:bg-surface-2"
                }`}
              >
                {cat} ({count})
              </button>
            );
          })}
        </div>
      </header>

      <div className="flex flex-col gap-6">
        {groups.map(({ key, label, items }) => {
          const isOpen = openMonths.has(key);
          return (
            <section key={key}>
              <button
                onClick={() => toggleMonth(key)}
                className="w-full flex items-center justify-between gap-3 mb-3 group"
              >
                <div className="flex items-center gap-3">
                  <h2 className="font-slab font-bold text-base text-navy-9 group-hover:text-brand-6 transition-colors">
                    {label}
                  </h2>
                  <span className="font-sans text-xs text-muted-foreground bg-surface-2 border border-border rounded-badge px-2 py-0.5">
                    {items.length}
                  </span>
                </div>
                <span className="text-muted-foreground text-sm transition-transform duration-150" style={{ transform: isOpen ? "rotate(0deg)" : "rotate(-90deg)" }}>
                  ▾
                </span>
              </button>

              {isOpen && (
                <div className="flex flex-col gap-3">
                  {items.map((s) => {
                    const thumb = firstThumbnail(s);
                    return (
                      <Link
                        key={s.event.id}
                        href={`/events/${s.event.id}`}
                        className="flex gap-3 bg-surface-0 border border-border rounded-badge-lg p-4 hover:border-brand-6 hover:shadow-md transition-all group"
                      >
                        {thumb && (
                          <div className="flex-shrink-0 w-24 h-16 rounded-badge overflow-hidden bg-surface-3">
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
                          <h3 className="font-slab font-semibold text-navy-9 group-hover:text-brand-6 transition-colors leading-snug mb-1">
                            {s.event.name}
                          </h3>
                          <p className="font-sans text-sm text-muted-foreground line-clamp-2 leading-relaxed">
                            {s.summary.topic.split("\n")[0]}
                          </p>
                          {s.entities.speakers.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {s.entities.speakers.slice(0, 4).map((sp, i) => (
                                <span
                                  key={i}
                                  className="font-sans text-xs bg-surface-2 text-muted-foreground px-2 py-0.5 rounded-badge"
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
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
}
