import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Image from "next/image";
import {
  getAllIds,
  getSummaryById,
  formatDate,
  qualityLabel,
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

  return (
    <article className="max-w-3xl mx-auto px-4 py-10">
      {/* Header */}
      <header className="mb-8">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="font-sans text-sm text-neutral-500">
            {formatDate(s.event.start_date)}
          </span>
          <CategoryBadge category={s.event.classification} />
          <QualityBadge quality={quality} />
        </div>
        <h1 className="font-slab font-bold text-2xl text-midnight leading-snug mb-4">
          {s.event.name}
        </h1>

        {/* Speakers */}
        {s.entities.speakers.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {s.entities.speakers.map((sp, i) => (
              <span
                key={i}
                className="font-sans text-xs bg-ink-wash border border-border-cream text-neutral-700 px-2 py-1 rounded"
              >
                {sp.name}
                {sp.affiliation && (
                  <span className="text-neutral-400"> · {sp.affiliation}</span>
                )}
              </span>
            ))}
          </div>
        )}
      </header>

      {/* Téma */}
      <section className="mb-8">
        <h2 className="font-slab font-semibold text-lg text-midnight mb-3">
          Téma
        </h2>
        <div className="font-slab text-base leading-relaxed whitespace-pre-line text-neutral-700">
          {s.summary.topic}
        </div>
      </section>

      {/* Hlavní body */}
      {s.summary.main_points.length > 0 && (
        <section className="mb-8">
          <h2 className="font-slab font-semibold text-lg text-midnight mb-3">
            Hlavní body
          </h2>
          <ul className="flex flex-col gap-3">
            {s.summary.main_points.map((point, i) => (
              <li key={i} className="font-slab text-sm leading-relaxed text-neutral-700 pl-4 border-l-2 border-border-cream">
                <MainPoint text={point} />
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Highlights */}
      {s.highlights && s.highlights.length > 0 && (
        <section className="mb-8">
          <h2 className="font-slab font-semibold text-lg text-midnight mb-4">
            Výrazné momenty
          </h2>
          <div className="flex flex-col gap-5">
            {s.highlights.map((h, i) => (
              <div
                key={i}
                className="border-l-4 border-crimson bg-crimson-tint rounded-r-lg p-4"
              >
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
                <blockquote className="font-slab text-base leading-relaxed text-midnight mb-2">
                  &ldquo;{h.text}&rdquo;
                </blockquote>
                <footer className="font-sans text-xs text-neutral-500 flex flex-wrap items-center gap-2">
                  <span className="font-medium text-neutral-700">{h.speaker}</span>
                  {h.affiliation && <span>· {h.affiliation}</span>}
                  <span className="font-mono">· {h.timestamp}</span>
                  <span className="px-1.5 py-0.5 bg-white border border-border-cream rounded">
                    {h.type === "citation" ? "citace" : "parafráze"}
                  </span>
                </footer>
                {h.context && (
                  <div className="mt-3 bg-teal-tint border-l-2 border-teal rounded-r p-3 font-sans text-xs text-neutral-700 leading-relaxed">
                    <span className="font-semibold text-teal uppercase tracking-wide text-[10px] block mb-1">Kontext</span>
                    {h.context}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Kontroverzní body */}
      {s.controversial && s.controversial.length > 0 && (
        <section className="mb-8">
          <h2 className="font-slab font-semibold text-lg text-midnight mb-4">
            Kontroverzní výroky
          </h2>
          <div className="flex flex-col gap-5">
            {s.controversial.map((c, i) => (
              <section
                key={i}
                aria-label="Kontroverzní výrok"
                className="border border-orange rounded-lg p-4 bg-orange-tint"
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
                <p className="font-slab text-base leading-relaxed text-midnight mb-2">
                  {c.statement}
                </p>
                <footer className="font-sans text-xs text-neutral-500 flex flex-wrap items-center gap-2">
                  <span className="font-medium text-neutral-700">{c.speaker}</span>
                  {c.affiliation && <span>· {c.affiliation}</span>}
                  <span className="font-mono">· {c.timestamp}</span>
                </footer>
                {c.context && (
                  <div className="mt-3 bg-white border-l-2 border-navy-purple rounded-r p-3 font-sans text-xs text-neutral-700 leading-relaxed">
                    <span className="font-semibold text-navy-purple uppercase tracking-wide text-[10px] block mb-1">Faktický kontext</span>
                    {c.context}
                  </div>
                )}
              </section>
            ))}
          </div>
        </section>
      )}

      {/* Výsledek */}
      <section className="mb-8">
        <h2 className="font-slab font-semibold text-lg text-midnight mb-3">
          Výsledek
        </h2>
        <div className="font-slab text-base leading-relaxed whitespace-pre-line text-neutral-700">
          {s.summary.outcome}
        </div>
      </section>

      {/* Poznámky k přepisu */}
      {s.summary.notes && (
        <section className="mb-8">
          <div className="border-l-4 border-orange bg-orange-tint rounded-r-lg p-4">
            <p className="font-sans text-xs font-semibold text-orange uppercase tracking-wide mb-1">
              Poznámky k přepisu
            </p>
            <p className="font-sans text-sm text-neutral-700 leading-relaxed">
              {s.summary.notes}
            </p>
          </div>
        </section>
      )}

      {/* Meta */}
      <footer className="border-t border-border-cream pt-4 font-sans text-xs text-neutral-400 flex flex-wrap gap-4">
        <span>Akce č. {s.event.id}</span>
        <span>
          Přepis: {s.transcription.parts_transcribed}/{s.transcription.parts_total} částí (
          {s.transcription.model})
        </span>
        <span>Souhrn: {s.model_hint}</span>
        <span>Vytvořeno: {new Date(s.created_at).toLocaleDateString("cs-CZ")}</span>
      </footer>
    </article>
  );
}

function MainPoint({ text }: { text: string }) {
  // Bold text between ** ** markers
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
