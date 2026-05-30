import type { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  getAllIds,
  getSummaryById,
  formatDate,
  qualityLabel,
  pluralCitace,
  pluralKontroverze,
} from "@/lib/summaries";
import { videoDeepLink, parseMainPointTimestamp } from "@/lib/types";
import { CategoryBadge } from "../../components/CategoryBadge";
import { QualityBadge } from "../../components/QualityBadge";
import { HighlightCard } from "../../components/HighlightCard";
import { ControversyCard } from "../../components/ControversyCard";
import { RenderMd } from "../../components/RenderMd";

function VideoLink({
  url,
  timestamp,
  subtle = false,
}: {
  url: string;
  timestamp: string;
  subtle?: boolean;
}) {
  const slash = timestamp.indexOf("/");
  const part = slash >= 0 ? timestamp.slice(0, slash) : timestamp;
  const time = slash >= 0 ? timestamp.slice(slash + 1) : timestamp;
  if (subtle) {
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        title="Přejít na videozáznam v archivu Poslanecké sněmovny"
        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-border text-muted-foreground hover:border-teal-6 hover:text-teal-6 font-sans text-xs transition-colors whitespace-nowrap"
      >
        ▶&nbsp;Záznam · část&nbsp;{part},&nbsp;{time}
      </a>
    );
  }
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      title="Přejít na videozáznam v archivu Poslanecké sněmovny"
      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-0 border border-teal-6 text-teal-7 hover:bg-teal-6 hover:text-white font-sans text-xs font-semibold transition-colors whitespace-nowrap"
    >
      ▶&nbsp;Záznam · část&nbsp;{part},&nbsp;{time}
    </a>
  );
}

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
  const description = s.summary.topic.split("\n")[0].slice(0, 200);
  return {
    title: s.event.name,
    description,
    openGraph: {
      title: s.event.name,
      description,
      type: "article",
      publishedTime: s.event.start_date,
    },
    twitter: {
      card: "summary_large_image",
      title: s.event.name,
      description,
    },
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
        <RenderMd
          text={s.summary.topic}
          className="font-slab text-base leading-relaxed text-foreground space-y-2"
        />
      </section>

      {/* Hlavní body */}
      {s.summary.main_points.length > 0 && (
        <section className="mb-8">
          <h2 className="font-slab font-semibold text-lg text-navy-9 mb-3">Hlavní body</h2>
          <ul className="flex flex-col gap-3">
            {s.summary.main_points.map((point, i) => {
              const { cleanText, timestamp } = parseMainPointTimestamp(point);
              const vlink = videoDeepLink(s.event.video_parts, timestamp);
              return (
                <li
                  key={i}
                  className="font-slab text-sm leading-relaxed text-foreground pl-4 border-l-2 border-border"
                >
                  <RenderMd text={cleanText} className="space-y-1" />
                  {vlink && timestamp && (
                    <div className="mt-1">
                      <VideoLink url={vlink} timestamp={timestamp} subtle />
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      )}

      {/* Výsledek */}
      <section className="mb-8">
        <h2 className="font-slab font-semibold text-lg text-navy-9 mb-3">Výsledek</h2>
        <RenderMd
          text={s.summary.outcome}
          className="font-slab text-base leading-relaxed text-foreground space-y-2"
        />
      </section>

      {/* Výrazné momenty */}
      {s.highlights && s.highlights.length > 0 && (
        <section className="mb-8">
          <h2 className="font-slab font-semibold text-lg text-navy-9 mb-4">Výrazné momenty</h2>
          <div className="flex flex-col gap-6">
            {s.highlights.map((h, i) => {
              const vlink = videoDeepLink(s.event.video_parts, h.timestamp);
              return (
                <div key={i} className="flex flex-col gap-2">
                  <HighlightCard
                    highlight={h}
                    eventName={s.event.name}
                    category={s.event.classification}
                    date={s.event.start_date}
                  />
                  {/* Type tag + optional video link */}
                  <div className="flex flex-wrap items-center gap-2 ml-1.5">
                    <span className="font-sans text-xs px-1.5 py-0.5 bg-surface-2 border border-border rounded text-muted-foreground">
                      {h.type === "citation" ? "citace" : "parafráze"}
                    </span>
                    {vlink && h.timestamp && (
                      <VideoLink url={vlink} timestamp={h.timestamp} />
                    )}
                  </div>
                  {/* Context */}
                  {h.context && (
                    <div className="bg-teal-0 border-l-2 border-teal-6 rounded-r p-3 font-sans text-xs text-foreground leading-relaxed ml-1.5">
                      <span className="font-semibold text-teal-6 uppercase tracking-wide text-[10px] block mb-1">
                        Kontext
                      </span>
                      {h.context}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Kontroverzní výroky */}
      {s.controversial && s.controversial.length > 0 && (
        <section className="mb-8">
          <h2 className="font-slab font-semibold text-lg text-navy-9 mb-4">
            Kontroverzní výroky
          </h2>
          <div className="flex flex-col gap-6">
            {s.controversial.map((c, i) => {
              const vlink = videoDeepLink(s.event.video_parts, c.timestamp);
              return (
                <div key={i} className="flex flex-col gap-2">
                  <ControversyCard
                    item={c}
                    eventName={s.event.name}
                    category={s.event.classification}
                    date={s.event.start_date}
                  />
                  {vlink && c.timestamp && (
                    <div className="ml-1.5">
                      <VideoLink url={vlink} timestamp={c.timestamp} />
                    </div>
                  )}
                  {c.context && (
                    <div className="bg-surface-0 border-l-2 border-navy-6 rounded-r p-3 font-sans text-xs text-foreground leading-relaxed ml-1.5">
                      <span className="font-semibold text-navy-6 uppercase tracking-wide text-[10px] block mb-1">
                        Faktický kontext
                      </span>
                      {c.context}
                    </div>
                  )}
                </div>
              );
            })}
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


