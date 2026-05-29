import Link from "next/link";
import Image from "next/image";
import { getAllSummaries, formatDate, firstThumbnail } from "@/lib/summaries";
import { CategoryBadge } from "./components/CategoryBadge";

export default function HomePage() {
  const all = getAllSummaries();
  const recent = all.slice(0, 10);

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <header className="mb-10">
        <h1 className="font-slab font-bold text-3xl text-navy-9 mb-3">
          PSP Video Archive
        </h1>
        <p className="font-slab text-lg text-muted-foreground max-w-2xl leading-relaxed">
          Strukturované souhrny akcí Poslanecké sněmovny ČR — semináře,
          konference, výbory. Přepisy pořízeny automaticky, souhrny zpracovány
          pomocí AI.
        </p>
        <div className="mt-4">
          <Link
            href="/events"
            className="inline-block bg-brand-6 text-surface-0 font-sans font-medium text-sm px-4 py-2 rounded hover:bg-brand-7 transition-colors"
          >
            Všechny akce →
          </Link>
        </div>
      </header>

      <section>
        <h2 className="font-slab font-semibold text-xl text-navy-9 mb-4">
          Nejnovější souhrny
        </h2>
        <div className="flex flex-col gap-3">
          {recent.map((s) => {
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
                  <h3 className="font-slab font-semibold text-navy-9 group-hover:text-brand-6 transition-colors leading-snug mb-1">
                    {s.event.name}
                  </h3>
                  <p className="font-sans text-sm text-muted-foreground line-clamp-2 leading-relaxed">
                    {s.summary.topic.split("\n")[0]}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
        {all.length > 10 && (
          <div className="mt-4 text-center">
            <Link
              href="/events"
              className="font-sans text-sm text-brand-6 hover:text-brand-7"
            >
              Zobrazit všech {all.length} akcí →
            </Link>
          </div>
        )}
      </section>
    </div>
  );
}
