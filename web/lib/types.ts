// Pure types and helpers — safe to import in client components

export interface Speaker {
  name: string;
  person_id: string | null;
  affiliation: string | null;
}

export interface VideoPart {
  part: number;
  url: string;
  from_sec?: number;
}

export interface HighlightItem {
  text: string;
  type: "citation" | "paraphrase";
  speaker: string;
  affiliation: string | null;
  timestamp: string;
  screenshot_path: string | null;
  context: string | null;
}

export interface ControversialItem {
  statement: string;
  speaker: string;
  affiliation: string | null;
  timestamp: string;
  screenshot_path: string | null;
  context: string | null;
}

export interface Summary {
  schema_version: string;
  model_hint: string;
  created_at: string;
  event: {
    id: string;
    name: string;
    classification: string;
    start_date: string;
    end_date: string | null;
    sources: string[];
    video_parts?: VideoPart[];
  };
  transcription: {
    parts_transcribed: number;
    parts_total: number;
    source: string;
    model: string;
  };
  summary: {
    topic: string;
    main_points: string[];
    outcome: string;
    notes: string | null;
  };
  entities: {
    speakers: Speaker[];
  };
  highlights: HighlightItem[] | null;
  controversial: ControversialItem[] | null;
}

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return `${d.getDate()}. ${d.getMonth() + 1}. ${d.getFullYear()}`;
}

export function qualityLabel(
  parts_transcribed: number,
  parts_total: number
): "good" | "partial" | "poor" {
  if (parts_total === 0) return "poor";
  const ratio = parts_transcribed / parts_total;
  if (ratio >= 0.9) return "good";
  if (ratio >= 0.5) return "partial";
  return "poor";
}

function isRemoteUrl(path: string | null | undefined): path is string {
  return typeof path === "string" && path.startsWith("http");
}

export function firstThumbnail(s: Summary): string | null {
  const candidates = [
    s.highlights?.[0]?.screenshot_path,
    s.controversial?.[0]?.screenshot_path,
  ];
  return candidates.find(isRemoteUrl) ?? null;
}

export function pluralCitace(n: number): string {
  if (n === 1) return "1 citace";
  if (n >= 2 && n <= 4) return `${n} citace`;
  return `${n} citací`;
}

export function pluralKontroverze(n: number): string {
  if (n === 1) return "1 kontroverze";
  if (n >= 2 && n <= 4) return `${n} kontroverze`;
  return `${n} kontroverzí`;
}

/** Build a PSP video deep-link for a given N/MM:SS timestamp and video parts list. */
export function videoDeepLink(
  videoParts: VideoPart[] | null | undefined,
  timestamp: string | null | undefined
): string | null {
  if (!timestamp || !videoParts?.length) return null;
  const m = timestamp.match(/^(\d+)\/(\d{1,2}):(\d{2})$/);
  if (!m) return null;
  const part = parseInt(m[1], 10);
  const secs = parseInt(m[2], 10) * 60 + parseInt(m[3], 10);
  const vp = videoParts.find((p) => p.part === part);
  if (!vp) return null;
  return `${vp.url}#t=${secs}`;
}

/**
 * Extract a trailing `[N/MM:SS]` timestamp (optionally in backticks) from a
 * main_points string. Returns the cleaned text and the timestamp separately.
 */
export function parseMainPointTimestamp(text: string): {
  cleanText: string;
  timestamp: string | null;
} {
  const m = text.match(/`?\[(\d+\/\d{1,2}:\d{2})\]`?\s*$/);
  if (!m) return { cleanText: text, timestamp: null };
  return { cleanText: text.slice(0, m.index).trimEnd(), timestamp: m[1] };
}
