import type { ReactNode } from "react";

/** Render inline **bold** spans. */
export function applyBold(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((p, i) =>
    p.startsWith("**") ? <strong key={i}>{p.slice(2, -2)}</strong> : p
  );
}

interface Props {
  text: string;
  className?: string;
  itemClassName?: string;
}

/**
 * Minimal markdown renderer: **bold** inline, bullet lists (* / -), paragraph breaks.
 * Does not pull in a full markdown library.
 */
export function RenderMd({ text, className, itemClassName }: Props) {
  const lines = text.split("\n");
  const blocks: ReactNode[] = [];
  let listItems: string[] = [];

  const flushList = () => {
    if (listItems.length === 0) return;
    blocks.push(
      <ul key={`ul-${blocks.length}`} className="list-disc list-outside ml-4 space-y-0.5">
        {listItems.map((item, i) => (
          <li key={i} className={itemClassName}>
            {applyBold(item)}
          </li>
        ))}
      </ul>
    );
    listItems = [];
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList();
      continue;
    }
    const bullet = trimmed.match(/^[*\-•]\s+(.*)/);
    if (bullet) {
      listItems.push(bullet[1]);
    } else {
      flushList();
      blocks.push(
        <p key={`p-${blocks.length}`} className={itemClassName}>
          {applyBold(trimmed)}
        </p>
      );
    }
  }
  flushList();

  return <div className={className}>{blocks}</div>;
}
