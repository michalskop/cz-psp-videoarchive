import type { Metadata } from "next";
import Link from "next/link";
import { getAllSummaries, formatDate, qualityLabel } from "@/lib/summaries";
import { CategoryBadge } from "../components/CategoryBadge";
import { QualityBadge } from "../components/QualityBadge";

export const metadata: Metadata = {
  title: "Archiv akcí",
  description: "Přehled všech zaznamenaných a shrnutých akcí Poslanecké sněmovny.",
};

export default function EventsPage() {
  const summaries = getAllSummaries();

  const categories = Array.from(
    new Set(summaries.map((s) => s.event.classification))
  ).sort();

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <header className="mb-8">
        <h1 className="font-slab font-bold text-2xl text-midnight mb-1">
          Archiv akcí PSP
        </h1>
        <p className="font-sans text-sm text-neutral-500">
          {summaries.length} akcí · kategorie:{" "}
          {categories.join(" · ")}
        </p>
      </header>

      <div className="flex flex-col gap-3">
        {summaries.map((s) => {
          const quality = qualityLabel(
            s.transcription.parts_transcribed,
            s.transcription.parts_total
          );
          const hasHighlights =
            s.highlights && s.highlights.length > 0;
          const hasControversies =
            s.controversial && s.controversial.length > 0;

          return (
            <Link
              key={s.event.id}
              href={`/events/${s.event.id}`}
              className="block bg-white border border-border-cream rounded-lg p-4 hover:border-crimson transition-colors group"
            >
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className="font-sans text-sm text-neutral-500">
                  {formatDate(s.event.start_date)}
                </span>
                <CategoryBadge category={s.event.classification} />
                <QualityBadge quality={quality} />
                {hasHighlights && (
                  <span className="font-sans text-xs text-crimson border border-crimson rounded px-1.5 py-0.5">
                    {s.highlights!.length} citací
                  </span>
                )}
                {hasControversies && (
                  <span className="font-sans text-xs text-orange border border-orange rounded px-1.5 py-0.5">
                    {s.controversial!.length} kontroverze
                  </span>
                )}
              </div>
              <h2 className="font-slab font-semibold text-midnight group-hover:text-crimson transition-colors leading-snug mb-1">
                {s.event.name}
              </h2>
              <p className="font-sans text-sm text-neutral-600 line-clamp-2 leading-relaxed">
                {s.summary.topic.split("\n")[0]}
              </p>
              {s.entities.speakers.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {s.entities.speakers.slice(0, 5).map((sp, i) => (
                    <span
                      key={i}
                      className="font-sans text-xs bg-ink-wash text-neutral-600 px-2 py-0.5 rounded"
                    >
                      {sp.name}
                    </span>
                  ))}
                  {s.entities.speakers.length > 5 && (
                    <span className="font-sans text-xs text-neutral-400">
                      +{s.entities.speakers.length - 5}
                    </span>
                  )}
                </div>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
