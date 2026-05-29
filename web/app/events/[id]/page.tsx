import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Image from "next/image";
import {
  getAllIds,
  getSummaryById,
  formatDate,
  qualityLabel,
  pluralCitace,
  pluralKontroverze,
} from "@/lib/summaries";
import { CategoryBadge } from "../../components/CategoryBadge";
import { QualityBadge } from "../../components/QualityBadge";

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateStaticParams() {
  return getAllIds().map((id) => ({ id }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const s = getSummaryById(id);
  if (!s) return {};
  return {
    title: s.event.name,
    description: s.summary.topic.split("\n")[0].slice(0, 200),
  };
}

export default async function EventPage({ params }: Props) {
  const { id } = await params;
  const s = getSummaryById(id);
  if (!s) notFound();

  const quality = qualityLabel(
    s.transcription.parts_transcribed,
    s.transcription.parts_total
  );
  const highlightCount = s.highlights?.length ?? 0;
  const controversyCount = s.controversial?.length ?? 0;

  return (
    <article className="max-w-3xl mx-auto px-4 py-10">
      {/* Header */}
      <header className="mb-8">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="font-sans text-sm text-muted-foreground">
            {formatDate(s.event.start_date)}
          </span>
          <CategoryBadge category={s.event.classification} />
          <QualityBadge quality={quality} />
          {highlightCount > 0 && (
            <span className="font-sans text-xs text-brand-6 border border-brand-6 rounded px-2 py-0.5">
              {pluralCitace(highlightCount)}
            </span>
          )}
          {controversyCount > 0 && (
            <span className="font-sans text-xs text-orange-6 border border-orange-6 rounded px-2 py-0.5">
              {pluralKontroverze(controversyCount)}
            </span>
          )}
        </div>
        <h1 className="font-slab font-bold text-2xl text-navy-9 leading-snug mb-4">
          {s.event.name}
        </h1>

        {/* Speakers */}
        {s.entities.speakers.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {s.entities.speakers.map((sp, i) => (
              <span
                key={i}
                className="font-sans text-xs bg-surface-2 border border-border text-foreground px-2 py-1 rounded"
              >
                {sp.name}
                {sp.affiliation && (
                  <span className="text-muted-foreground"> · {sp.affiliation}</span>
                )}
              </span>
            ))}
          </div>
        )}
      </header>

      {/* Téma */}
      <section className="mb-8">
        <h2 className="font-slab font-semibold text-lg text-navy-9 mb-3">Téma</h2>
        <div className="font-slab text-base leading-relaxed whitespace-pre-line text-foreground">
          {s.summary.topic}
        </div>
      </section>

      {/* Hlavní body */}
      {s.summary.main_points.length > 0 && (
        <section className="mb-8">
          <h2 className="font-slab font-semibold text-lg text-navy-9 mb-3">Hlavní body</h2>
          <ul className="flex flex-col gap-3">
            {s.summary.main_points.map((point, i) => (
              <li
                key={i}
                className="font-slab text-sm leading-relaxed text-foreground pl-4 border-l-2 border-border"
              >
                <MainPoint text={point} />
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Výsledek */}
      <section className="mb-8">
        <h2 className="font-slab font-semibold text-lg text-navy-9 mb-3">Výsledek</h2>
        <div className="font-slab text-base leading-relaxed whitespace-pre-line text-foreground">
          {s.summary.outcome}
        </div>
      </section>

      {/* Výrazné momenty */}
      {s.highlights && s.highlights.length > 0 && (
        <section className="mb-8">
          <h2 className="font-slab font-semibold text-lg text-navy-9 mb-4">Výrazné momenty</h2>
          <div className="flex flex-col gap-5">
            {s.highlights.map((h, i) => (
              <div key={i} className="border-l-4 border-brand-6 bg-brand-0 rounded-r-lg p-4">
                {h.screenshot_path && (
                  <div className="mb-3 rounded overflow-hidden">
                    <Image
                      src={h.screenshot_path}
                      alt={`Screenshot — ${h.speaker}`}
                      width={800}
                      height={450}
                      className="w-full object-cover"
                      unoptimized
                    />
                  </div>
                )}
                <blockquote className="font-slab text-base leading-relaxed text-navy-9 mb-2">
                  &ldquo;{h.text}&rdquo;
                </blockquote>
                <footer className="font-sans text-xs text-muted-foreground flex flex-wrap items-center gap-2">
                  <span className="font-medium text-foreground">{h.speaker}</span>
                  {h.affiliation && <span>· {h.affiliation}</span>}
                  <span className="font-mono">· {h.timestamp}</span>
                  <span className="px-1.5 py-0.5 bg-surface-0 border border-border rounded">
                    {h.type === "citation" ? "citace" : "parafráze"}
                  </span>
                </footer>
                {h.context && (
                  <div className="mt-3 bg-teal-0 border-l-2 border-teal-6 rounded-r p-3 font-sans text-xs text-foreground leading-relaxed">
                    <span className="font-semibold text-teal-6 uppercase tracking-wide text-[10px] block mb-1">
                      Kontext
                    </span>
                    {h.context}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Kontroverzní výroky */}
      {s.controversial && s.controversial.length > 0 && (
        <section className="mb-8">
          <h2 className="font-slab font-semibold text-lg text-navy-9 mb-4">
            Kontroverzní výroky
          </h2>
          <div className="flex flex-col gap-5">
            {s.controversial.map((c, i) => (
              <section
                key={i}
                aria-label="Kontroverzní výrok"
                className="border border-orange-6 rounded-lg p-4 bg-orange-0"
              >
                {c.screenshot_path && (
                  <div className="mb-3 rounded overflow-hidden">
                    <Image
                      src={c.screenshot_path}
                      alt={`Screenshot — ${c.speaker}`}
                      width={800}
                      height={450}
                      className="w-full object-cover"
                      unoptimized
                    />
                  </div>
                )}
                <ControversialStatement text={c.statement} />
                <footer className="font-sans text-xs text-muted-foreground flex flex-wrap items-center gap-2 mt-2">
                  <span className="font-medium text-foreground">{c.speaker}</span>
                  {c.affiliation && <span>· {c.affiliation}</span>}
                  <span className="font-mono">· {c.timestamp}</span>
                </footer>
                {c.context && (
                  <div className="mt-3 bg-surface-0 border-l-2 border-navy-6 rounded-r p-3 font-sans text-xs text-foreground leading-relaxed">
                    <span className="font-semibold text-navy-6 uppercase tracking-wide text-[10px] block mb-1">
                      Faktický kontext
                    </span>
                    {c.context}
                  </div>
                )}
              </section>
            ))}
          </div>
        </section>
      )}

      {/* Poznámky k přepisu */}
      {s.summary.notes && (
        <section className="mb-8">
          <div className="border-l-4 border-orange-6 bg-orange-0 rounded-r-lg p-4">
            <p className="font-sans text-xs font-semibold text-orange-6 uppercase tracking-wide mb-1">
              Poznámky k přepisu
            </p>
            <p className="font-sans text-sm text-foreground leading-relaxed">
              {s.summary.notes}
            </p>
          </div>
        </section>
      )}

      {/* Meta */}
      <footer className="border-t border-border pt-4 font-sans text-xs text-muted-foreground flex flex-wrap gap-4">
        <span>Akce č. {s.event.id}</span>
        <span>
          Přepis: {s.transcription.parts_transcribed}/{s.transcription.parts_total} částí (
          {s.transcription.model})
        </span>
        <span>Souhrn: {s.model_hint}</span>
        <span>
          Vytvořeno: {new Date(s.created_at).getDate()}. {new Date(s.created_at).getMonth() + 1}. {new Date(s.created_at).getFullYear()}
        </span>
      </footer>
    </article>
  );
}

function MainPoint({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <>
      {parts.map((p, i) =>
        p.startsWith("**") ? (
          <strong key={i}>{p.slice(2, -2)}</strong>
        ) : (
          <span key={i}>{p}</span>
        )
      )}
    </>
  );
}

/**
 * Renders a controversial statement that may contain markdown bullet points.
 * Format expected (optional):
 *   Title line
 *
 *   *   **Kdo:** ...
 *   *   **Co:** ...
 *   *   **Proč:** ...
 *   *   **Čas:** ...   ← stripped (shown in footer)
 */
function ControversialStatement({ text }: { text: string }) {
  const lines = text.split("\n");
  const titleLines: string[] = [];
  const bullets: { key: string; value: string }[] = [];

  for (const line of lines) {
    const bulletMatch = line.match(/^\s*\*\s+\*\*([^:*]+):\*\*\s*(.*)/);
    if (bulletMatch) {
      const key = bulletMatch[1].trim();
      if (key === "Čas") continue; // already in footer
      bullets.push({ key, value: bulletMatch[2].trim() });
    } else if (!line.trim()) {
      if (titleLines.length > 0) continue; // skip blank lines after title
    } else if (bullets.length === 0) {
      titleLines.push(line);
    }
  }

  const title = titleLines.join(" ").trim();

  return (
    <div>
      {title && (
        <p className="font-slab text-base font-semibold leading-snug text-navy-9 mb-2">
          {title}
        </p>
      )}
      {bullets.length > 0 && (
        <dl className="font-sans text-sm text-foreground leading-relaxed space-y-1">
          {bullets.map(({ key, value }, i) => (
            <div key={i} className="flex gap-2">
              <dt className="font-semibold flex-shrink-0 text-muted-foreground">{key}:</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      )}
      {!title && bullets.length === 0 && (
        <p className="font-slab text-base leading-relaxed text-foreground">{text}</p>
      )}
    </div>
  );
}
