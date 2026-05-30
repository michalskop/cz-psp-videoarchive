# Design System — PSP Video Archive

Adapted from the DataTimes / Mahdalová & Škop design system. The same visual identity applies here: warm newsprint, crimson authority, slab serif credibility — applied to parliamentary transparency data rather than election models.

---

## 1. Visual Theme & Atmosphere

The PSP Video Archive is a record of public power — who said what, when, in which committee room. The interface must communicate seriousness and accountability. It borrows the DataTimes personality: a cream-tinted canvas (`#fdfbf7`) that suggests a quality newspaper archive, not a social feed.

The crimson accent (`#de1743`) marks editorially important elements — controversy badges, highlight markers, category labels. It is the red of a correction notice, not a notification bell.

**Key Characteristics:**
- Warm cream canvas (`#fdfbf7`) — newsprint, not digital white
- Roboto Slab (serif) for all editorial text: summaries, quotes, speaker names
- Work Sans (sans-serif) for UI chrome: filters, metadata, navigation, data tables
- Crimson (`#de1743`) — controversy badges, highlight borders, primary links
- Exclusively warm neutrals — no cold grays anywhere
- Light-mode only (dark variant not yet designed)

---

## 2. Color Palette

Identical to the DataTimes base system. Reference names and hex values are canonical — always use the name in component code, never a raw hex.

### Primary
| Name | Hex | Use |
|------|-----|-----|
| Crimson Brand | `#de1743` | Controversy badges, highlight borders, links, primary buttons, category labels |
| Crimson Hover | `#c5143c` | Hover state for brand links |
| Crimson Active | `#a81134` | Active/visited state |
| Crimson Tint | `#fff4f6` | Background for controversy InfoBox |

### Backgrounds & Surfaces
| Name | Hex | Use |
|------|-----|-----|
| Newsprint | `#fdfbf7` | Page background, all cards — never substitute pure white |
| Ink Wash | `#f8f6f0` | Blockquotes, fact-check annotation backgrounds, table headers |
| Border Cream | `#e8e8dc` | Card borders, dividers, separators |
| Pure White | `#ffffff` | Text on coloured surfaces only |

### Semantic Accents
| Name | Hex | Use |
|------|-----|-----|
| Navy Purple | `#6267a3` | Context/annotation InfoBox — fact-check notes |
| Teal | `#0e839e` | Verified/confirmed finding InfoBox |
| Teal Tint | `#e5fdfc` | Teal InfoBox background |
| Orange | `#f76800` | Warning InfoBox — transcript quality caveats |
| Orange Tint | `#fff3e8` | Warning InfoBox background |
| Midnight | `#272a59` | Dark surfaces — speaker profile headers, pull-quote cards |

### Category Badge Colours (PSP-specific)
| Category | Background | Use |
|----------|-----------|-----|
| Seminář | Crimson Brand `#de1743` | Expert seminar |
| Konference | Crimson Brand `#de1743` | Conference |
| Kulatý stůl | Navy Purple `#6267a3` | Round table |
| Veřejné slyšení | Teal `#0e839e` | Public hearing |
| Tiskové konference | Ink Wash `#f8f6f0` + Border Cream border | Press conference |
| Jednání výborů | Midnight `#272a59` | Committee meeting |
| Ostatní | Border Cream `#e8e8dc` | Other |

---

## 3. Typography

| Role | Font | Size | Weight | Line-height |
|------|------|------|--------|-------------|
| Event title (h1) | Roboto Slab | 2rem+ | 700 | 1.2 |
| Section heading (h2) | Roboto Slab | 1.5rem | 600–700 | 1.25 |
| Speaker name / sub-heading (h3) | Roboto Slab | 1.25rem | 600 | 1.30 |
| Summary body text | Roboto Slab | 1rem | 400 | 1.65 |
| Highlight quote | Roboto Slab | 1.1rem | 500 | 1.5 |
| UI labels, metadata, dates | Work Sans | 0.875rem | 400–500 | 1.4 |
| Category badge | Work Sans | 0.75rem | 500 | 1.0 |
| Data tables, timestamps | Work Sans | 0.875rem | 400 | 1.5 |

```css
@import url('https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@400;500;600;700&family=Work+Sans:wght@400;500;600;700&display=swap');

/* Editorial (summaries, quotes, speaker names) */
font-family: 'Roboto Slab', Georgia, serif;

/* UI / data (filters, metadata, tables) */
font-family: 'Work Sans', system-ui, sans-serif;
```

---

## 4. PSP-Specific Components

### EventCard
Used in event lists and search results.

- Background: Newsprint (`#fdfbf7`)
- Category badge: pill shape, colour from Category Badge table above, Work Sans 0.75rem
- Date: Work Sans, muted gray (`#888`), Czech locale (`cs-CZ`)
- Event title: Roboto Slab, links in Crimson Brand — hover to Crimson Hover
- Topic excerpt: 1–2 sentence lead, Roboto Slab body, capped at 2 lines
- Transcript quality indicator: small dot — green (good), amber (partial), red (poor)
- Bottom: speaker chip row (up to 5, then "+N more")
- Border: 1px Border Cream (`#e8e8dc`), 8px radius, subtle lift shadow on hover

### HighlightCard
Used in the highlights section of a summary detail page.

- Background: Newsprint (`#fdfbf7`)
- Left border: 4px solid Crimson Brand (`#de1743`)
- Screenshot image: top, full-width, proportional — loaded from B2
- Type badge: "citace" (Crimson Brand) or "parafrá ze" (Navy Purple `#6267a3`)
- Quote text: Roboto Slab 1.1rem, weight 500, with large Crimson Brand opening quotation mark
- Speaker line: Work Sans 0.875rem — name (bold) + affiliation
- Timestamp: Work Sans small, muted — links to video position if available
- Fact-check context: collapsed behind "Kontext" toggle, renders as InfoBox info when open

### ControversyBlock
Used in the controversies section.

- InfoBox `error` style: 4px left border Crimson Brand (`#de1743`), Crimson Tint (`#fff4f6`) background
- Statement text: Roboto Slab body
- Controversy reason: italic, slightly smaller
- Fact-check annotation: InfoBox `info` (Navy Purple) nested below when `context` is non-null
- Speaker + timestamp: Work Sans small, right-aligned

### SpeakerChip
Inline speaker reference — used in event card footers and speaker lists.

- Background: Ink Wash (`#f8f6f0`)
- Border: 1px Border Cream
- Font: Work Sans 0.875rem
- Hover: Border Cream deepens, slight background shift
- Pill shape (border-radius: 9999px)
- If `person_id` is set: links to `/speakers/[id]`

### TranscriptQualityBadge
- `good`: Teal (`#0e839e`) dot
- `partial`: Orange (`#f76800`) dot
- `poor`: Crimson Brand (`#de1743`) dot
- Label: Work Sans 0.75rem, muted

### SummarySection (InfoBox usage in detail page)
| Section content | InfoBox type |
|-----------------|-------------|
| Fact-check context on highlight | Info (Navy Purple) |
| Controversial statement | Error (Crimson) |
| Transcript quality caveat / notes | Warning (Orange) |
| Confirmed finding / positive outcome | Success (Teal) |

---

## 5. Layout

- **Article body** (summary detail): single column, max 720px centered — reading width, not dashboard width
- **Event list grid**: 3 columns desktop → 2 tablet → 1 mobile
- **Container max**: ~1100px for grids, 720px for article content
- **Vertical rhythm**: generous — 48–80px between major sections
- **Left crimson stripe**: 4px solid Crimson Brand on left edge of highlight and controversy cards — the signature InfoBox depth signal

### Spacing Scale
4 · 8 · 12 · 16 · 20 · 24 · 32 · 48 · 64 · 80 (px, base unit 4px)

---

## 6. Structured Data (JSON-LD)

Every page type has a required JSON-LD block for AI/search discoverability.

| Page | Schema type |
|------|-------------|
| Homepage | `WebSite` + `Dataset` |
| Event detail | `Event` + `Article` |
| Speaker page | `Person` |
| Event list | `CollectionPage` + `Dataset` |

See `plans/agent-ready.md` for exact JSON-LD templates.

---

## 7. Do's and Don'ts

### Do
- Use Newsprint (`#fdfbf7`) for every card and page background
- Use Roboto Slab for all summary and quote text; Work Sans for UI chrome and metadata
- Use the Category Badge colour map — don't invent new badge colours
- Apply InfoBox types semantically: `error` for controversy, `info` for fact-check, `warning` for transcript quality
- Keep the left crimson stripe on HighlightCard and ControversyBlock — it is the signature depth signal

### Don't
- Don't use pure white (`#ffffff`) as a page or card background
- Don't use Roboto Slab for data tables, timestamps, or filter UI — use Work Sans there
- Don't implement dark mode — not yet designed
- Don't add new category badge colours without updating this document
- Don't use drop shadows heavier than `0 2px 8px rgba(0,0,0,0.08)`

---

## 8. Agent Prompt Guide

When asking an AI to build or extend components, use these reference phrases:

- **Page background**: "Newsprint (`#fdfbf7`)"
- **Card left accent**: "4px solid Crimson Brand (`#de1743`) left border"
- **Controversy block**: "InfoBox error style — Crimson Tint (`#fff4f6`) background, Crimson Brand left border"
- **Fact-check note**: "InfoBox info style — light navy tint background, Navy Purple (`#6267a3`) left border"
- **Category badge**: "pill badge, Work Sans 0.75rem, colour from Category Badge table"
- **Speaker chip**: "Ink Wash (`#f8f6f0`) background, pill shape, Work Sans 0.875rem"
- **Quote text**: "Roboto Slab 1.1rem weight 500, large Crimson Brand opening quotation mark"
- **Dark surface** (pull-quote, speaker header): "Midnight (`#272a59`) background, Pure White text"

---

*Canonical upstream: [mahdalova-skop/DESIGN.md](https://github.com/michalskop/mahdalova-skop/blob/main/DESIGN.md)*  
*PSP-specific tokens and components defined here take precedence for this project.*
