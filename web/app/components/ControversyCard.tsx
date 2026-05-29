import Image from "next/image";
import type { ControversialItem } from "@/lib/types";
import { formatDate } from "@/lib/types";
import { PspLogotype } from "./PspLogotype";
import { applyBold, RenderMd } from "./RenderMd";

interface Props {
  item: ControversialItem;
  eventName: string;
  category: string;
  date: string;
}

export function ControversyCard({ item, eventName, category, date }: Props) {
  const { title, bullets } = parseStatement(item.statement);

  return (
    <div
      aria-label="Kontroverzní výrok"
      className="flex rounded-lg overflow-hidden shadow-md bg-surface-1 max-w-xl"
    >
      {/* Left orange strip */}
      <div className="w-1.5 flex-shrink-0 bg-orange-6" />

      {/* Card body */}
      <div className="flex flex-col flex-1 min-w-0">

        {/* Screenshot */}
        {item.screenshot_path && (
          <div className="w-full aspect-[16/9] overflow-hidden bg-surface-3">
            <Image
              src={item.screenshot_path}
              alt={`Screenshot — ${item.speaker}`}
              width={800}
              height={450}
              className="w-full h-full object-cover"
              unoptimized
            />
          </div>
        )}

        {/* Content */}
        <div className="px-5 pt-4 pb-5 flex flex-col gap-3">
          {/* Badge */}
          <div>
            <span className="inline-block bg-orange-6 text-surface-0 font-sans font-bold text-[10px] uppercase tracking-widest px-2.5 py-1 rounded-sm">
              Kontroverze · {category}
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

          {/* Statement */}
          <div className="font-slab text-navy-9 leading-snug">
            {title && (
              <p className="text-xl font-bold mb-2">{applyBold(title)}</p>
            )}
            {bullets.length > 0 && (
              <dl className="font-sans text-sm text-foreground leading-relaxed space-y-1">
                {bullets.map(({ key, value }, i) => (
                  <div key={i} className="flex gap-2">
                    <dt className="font-semibold flex-shrink-0 text-orange-6">{key}:</dt>
                    <dd>{applyBold(value)}</dd>
                  </div>
                ))}
              </dl>
            )}
            {!title && bullets.length === 0 && (
              <RenderMd
                text={item.statement}
                className="text-xl font-bold"
                itemClassName="mb-1"
              />
            )}
          </div>

          {/* Divider */}
          <hr className="border-border" />

          {/* Attribution + logotype */}
          <div className="flex items-end justify-between gap-2">
            <p className="font-sans text-xs leading-relaxed">
              <span className="font-bold text-orange-6 uppercase tracking-wide">
                {item.speaker}
              </span>
              {item.affiliation && (
                <span className="text-muted-foreground">{", "}{item.affiliation}</span>
              )}
              {item.timestamp && (
                <span className="text-muted-foreground">{" · "}{item.timestamp}</span>
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

function parseStatement(text: string): {
  title: string;
  bullets: { key: string; value: string }[];
} {
  const lines = text.split("\n");
  const titleLines: string[] = [];
  const bullets: { key: string; value: string }[] = [];

  for (const line of lines) {
    const m = line.match(/^\s*\*\s+\*\*([^:*]+):\*\*\s*(.*)/);
    if (m) {
      const key = m[1].trim();
      if (key === "Čas") continue;
      bullets.push({ key, value: m[2].trim() });
    } else if (line.trim() && bullets.length === 0) {
      titleLines.push(line.trim());
    }
  }

  return { title: titleLines.join(" "), bullets };
}
