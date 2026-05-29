import Link from "next/link";
import { getAllSummaries, formatDate, qualityLabel } from "@/lib/summaries";
import { CategoryBadge } from "./components/CategoryBadge";
import { QualityBadge } from "./components/QualityBadge";

export default function HomePage() {
  const all = getAllSummaries();
  const recent = all.slice(0, 10);

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <header className="mb-10">
        <h1 className="font-slab font-bold text-3xl text-midnight mb-3">
          PSP Video Archive
        </h1>
        <p className="font-slab text-lg text-neutral-600 max-w-2xl leading-relaxed">
          Strukturované souhrny akcí Poslanecké sněmovny ČR — semináře,
          konference, výbory. Přepisy pořízeny automaticky, souhrny zpracovány
          pomocí AI.
        </p>
        <div className="mt-4">
          <Link
            href="/events"
            className="inline-block bg-crimson text-white font-sans font-medium text-sm px-4 py-2 rounded hover:bg-crimson-hover transition-colors"
          >
            Všechny akce →
          </Link>
        </div>
      </header>

      <section>
        <h2 className="font-slab font-semibold text-xl text-midnight mb-4">
          Nejnovější souhrny
        </h2>
        <div className="flex flex-col gap-3">
          {recent.map((s) => {
            const quality = qualityLabel(
              s.transcription.parts_transcribed,
              s.transcription.parts_total
            );
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
                </div>
                <h3 className="font-slab font-semibold text-midnight group-hover:text-crimson transition-colors leading-snug mb-1">
                  {s.event.name}
                </h3>
                <p className="font-sans text-sm text-neutral-600 line-clamp-2 leading-relaxed">
                  {s.summary.topic.split("\n")[0]}
                </p>
              </Link>
            );
          })}
        </div>
        {all.length > 10 && (
          <div className="mt-4 text-center">
            <Link
              href="/events"
              className="font-sans text-sm text-crimson hover:text-crimson-hover"
            >
              Zobrazit všech {all.length} akcí →
            </Link>
          </div>
        )}
      </section>
    </div>
  );
}
