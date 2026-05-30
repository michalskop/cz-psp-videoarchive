"use client";

import { useEffect } from "react";

const CANONICAL = "https://snemovna.datatimes.cz/digest";

type AnyObj = Record<string, unknown>;

export function WebMCP() {
  useEffect(() => {
    if (typeof navigator === "undefined") return;
    const ctx = (navigator as unknown as AnyObj & { modelContext?: AnyObj }).modelContext;
    if (typeof ctx?.provideContext !== "function") return;

    (ctx.provideContext as (opts: AnyObj) => void)({
      tools: [
        {
          name: "list_events",
          description:
            "List Czech Parliament (PSP) events with AI-structured summaries. " +
            "Returns id, name, date, category, topic excerpt, and speaker list.",
          inputSchema: {
            type: "object",
            properties: {
              category: {
                type: "string",
                description:
                  "Filter by event category (optional). " +
                  "Common values: 'Semináře', 'Tiskové konference', 'Výbory', 'Konference', 'Kulaté stoly'.",
              },
              limit: {
                type: "number",
                description: "Maximum results to return (default 20, max 100).",
              },
            },
          },
          execute: async ({ category, limit = 20 }: { category?: string; limit?: number }) => {
            const res = await fetch(`${CANONICAL}/api/events.json`);
            if (!res.ok) return { error: "Could not load events" };
            const events = await res.json() as AnyObj[];
            const filtered = category
              ? events.filter((e) => e.category === category)
              : events;
            return filtered.slice(0, Math.min(limit, 100));
          },
        },
        {
          name: "get_event_summary",
          description:
            "Get the AI-structured summary for a specific Czech Parliament event. " +
            "Returns event metadata including name, date, category, topic description, and speakers.",
          inputSchema: {
            type: "object",
            properties: {
              id: {
                type: "string",
                description: "Event ID (numeric string, e.g. '2955'). Obtain IDs from list_events.",
              },
            },
            required: ["id"],
          },
          execute: async ({ id }: { id: string }) => {
            const res = await fetch(`${CANONICAL}/events/${id}`);
            if (!res.ok) return { error: "Event not found", id };
            const html = await res.text();
            // Extract the first JSON-LD block (Event+Article schema we embed on every event page)
            const match = html.match(
              /<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/
            );
            if (match) {
              try { return JSON.parse(match[1]); } catch { /* fall through */ }
            }
            return { error: "Could not parse event data", id };
          },
        },
      ],
    });
  }, []);

  return null;
}
