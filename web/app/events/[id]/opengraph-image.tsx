import { ImageResponse } from "next/og";
import { getAllIds, getSummaryById } from "@/lib/summaries";

export const dynamic = "force-static";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const robotoSlabBold = fetch(
  "https://raw.githubusercontent.com/googlefonts/robotoslab/main/fonts/ttf/RobotoSlab-Bold.ttf"
).then((r) => r.arrayBuffer());

const robotoSlabRegular = fetch(
  "https://raw.githubusercontent.com/googlefonts/robotoslab/main/fonts/ttf/RobotoSlab-Regular.ttf"
).then((r) => r.arrayBuffer());

const NEWSPRINT = "#fdfbf7";
const CRIMSON   = "#de1743";
const NAVY9     = "#101432";
const NAVY6     = "#6267a3";
const YELLOW7   = "#efb704";
const BORDER    = "#e8e8dc";
const SURFACE2  = "#f8f6f0";

const CATEGORY_COLOR: Record<string, string> = {
  "Seminář":            CRIMSON,
  "Konference":         CRIMSON,
  "Kulatý stůl":        NAVY6,
  "Veřejné slyšení":    "#0e839e",
  "Tiskové konference": NAVY9,
  "Jednání výborů":     "#272a59",
};

export async function generateStaticParams() {
  return getAllIds().map((id) => ({ id }));
}

interface Props {
  params: Promise<{ id: string }>;
}

export default async function OgImage({ params }: Props) {
  const { id } = await params;
  const s = getSummaryById(id);
  const [boldFont, regularFont] = await Promise.all([robotoSlabBold, robotoSlabRegular]);

  const title = s?.event.name ?? "Sněmovna Digest";
  const topic  = s?.summary.topic.split("\n")[0].slice(0, 160) ?? "";
  const date   = s ? (() => {
    const d = new Date(s.event.start_date);
    return `${d.getDate()}. ${d.getMonth() + 1}. ${d.getFullYear()}`;
  })() : "";
  const category = s?.event.classification ?? "";
  const badgeColor = CATEGORY_COLOR[category] ?? NAVY9;
  const firstQuote = s?.highlights?.[0]?.text.slice(0, 120) ?? null;
  const speaker    = s?.highlights?.[0]?.speaker ?? null;

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          background: NEWSPRINT,
          fontFamily: "Roboto Slab, Georgia, serif",
        }}
      >
        {/* Left crimson strip */}
        <div style={{ width: 16, background: CRIMSON, flexShrink: 0 }} />

        {/* Content */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            padding: "48px 64px 44px 56px",
          }}
        >
          {/* Top: logotype + date/category */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
              <span style={{ color: CRIMSON, fontWeight: 700, fontSize: 20 }}>Sněmovna</span>
              <span style={{ color: YELLOW7, fontWeight: 700, fontSize: 20 }}>.</span>
              <span style={{ color: NAVY9, fontWeight: 700, fontSize: 20 }}>DataTimes</span>
              <span style={{ color: YELLOW7, fontWeight: 700, fontSize: 20 }}>.</span>
              <span style={{ color: NAVY9, fontWeight: 700, fontSize: 20 }}>cz</span>
              <span style={{ color: NAVY6, fontWeight: 700, fontSize: 20 }}>/digest</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              {date && (
                <span style={{ color: NAVY6, fontSize: 18, fontWeight: 400 }}>{date}</span>
              )}
              {category && (
                <span
                  style={{
                    background: badgeColor,
                    color: "#fff",
                    fontSize: 13,
                    fontWeight: 700,
                    letterSpacing: "0.1em",
                    padding: "5px 14px",
                    borderRadius: 4,
                    textTransform: "uppercase",
                  }}
                >
                  {category}
                </span>
              )}
            </div>
          </div>

          {/* Middle: event title + quote */}
          <div style={{ display: "flex", flexDirection: "column", gap: 24, flex: 1, justifyContent: "center" }}>
            <span
              style={{
                color: NAVY9,
                fontSize: title.length > 60 ? 42 : 52,
                fontWeight: 700,
                lineHeight: 1.2,
                letterSpacing: "-0.3px",
              }}
            >
              {title}
            </span>

            {firstQuote ? (
              <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                <span style={{ color: CRIMSON, fontSize: 48, lineHeight: 1, fontWeight: 700, marginTop: -8 }}>
                  &ldquo;
                </span>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <span style={{ color: NAVY9, fontSize: 22, fontWeight: 400, lineHeight: 1.5 }}>
                    {firstQuote}{firstQuote.length >= 120 ? "…" : ""}
                  </span>
                  {speaker && (
                    <span style={{ color: CRIMSON, fontSize: 16, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>
                      {speaker}
                    </span>
                  )}
                </div>
              </div>
            ) : topic ? (
              <span style={{ color: NAVY6, fontSize: 24, fontWeight: 400, lineHeight: 1.5 }}>
                {topic}{topic.length >= 160 ? "…" : ""}
              </span>
            ) : null}
          </div>

          {/* Bottom strip */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              borderTop: `2px solid ${BORDER}`,
              paddingTop: 18,
            }}
          >
            {s?.entities.speakers.slice(0, 4).map((sp) => sp.name).join(" · ") && (
              <span style={{ color: NAVY6, fontSize: 16, fontWeight: 400 }}>
                {s!.entities.speakers.slice(0, 4).map((sp) => sp.name).join(" · ")}
                {s!.entities.speakers.length > 4 ? " · …" : ""}
              </span>
            )}
            <div
              style={{
                background: SURFACE2,
                border: `1px solid ${BORDER}`,
                borderRadius: 8,
                padding: "6px 18px",
                display: "flex",
                alignItems: "center",
                marginLeft: "auto",
              }}
            >
              <span style={{ color: NAVY9, fontSize: 15, fontWeight: 700 }}>datatimes.cz</span>
            </div>
          </div>
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [
        { name: "Roboto Slab", data: boldFont,    weight: 700, style: "normal" },
        { name: "Roboto Slab", data: regularFont, weight: 400, style: "normal" },
      ],
    }
  );
}
