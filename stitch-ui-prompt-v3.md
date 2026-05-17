# Stitch UI Prompt v3: APP Commercial Decision Dashboard

## Design References (MUST follow these styles)
- **Primary reference: Stripe Dashboard** — The gold standard for fintech analytics UI. Clean metric strips, rigorous color discipline, zero-baseline charts.
- **Secondary reference: Linear.app** — Dark-first, speed-obsessed, glanceable density. Every element earns its place.
- **Inspiration: Dribbble 2025 dark dashboards** — Glassmorphism cards, neon semantic accents, high data density with breathing room.

---

## Global Design System

### Color Palette (Dark Mode Default)
| Token | Value | Usage |
|-------|-------|-------|
| `--bg-base` | `#0a0a0f` | Page background (near-black, NOT pure black) |
| `--bg-surface` | `#13131f` | Card surfaces |
| `--bg-elevated` | `#1a1a2e` | Elevated cards (hover states, modals) |
| `--border-subtle` | `rgba(255,255,255,0.06)` | Card borders (NO heavy borders, use subtle glow) |
| `--text-primary` | `#f1f5f9` | Primary text (off-white, NOT pure white) |
| `--text-secondary` | `#94a3b8` | Secondary text, labels |
| `--text-tertiary` | `#64748b` | Metadata, timestamps |
| `--accent-primary` | `#3b82f6` | Brand accent (blue) |
| `--accent-gradient` | `linear-gradient(135deg, #3b82f6, #8b5cf6)` | Hero elements, active states |
| `--success` | `#10b981` | Positive change, growth |
| `--danger` | `#ef4444` | Negative change, alerts |
| `--warning` | `#f59e0b` | Caution, attention needed |
| `--chart-1` | `#3b82f6` | Primary chart color |
| `--chart-2` | `#8b5cf6` | Secondary chart color |
| `--chart-3` | `#06b6d4` | Tertiary chart color |
| `--chart-4` | `#10b981` | Quaternary chart color |
| `--chart-5` | `#f59e0b` | Quinary chart color |
| `--glow-success` | `rgba(16,185,129,0.15)` | Success card glow |
| `--glow-danger` | `rgba(239,68,68,0.15)` | Danger card glow |

### Typography
- **Font family**: "Inter" for numbers and English, "Noto Sans SC" for Chinese
- **Metric numbers**: 40px, font-weight 700, letter-spacing -0.02em, tabular nums
- **Card titles**: 16px, font-weight 600, `--text-primary`
- **Labels**: 13px, font-weight 500, `--text-secondary`
- **Body**: 14px, font-weight 400, `--text-secondary`

### Spacing & Layout
- **Page padding**: 32px
- **Card gap**: 20px
- **Card padding**: 24px
- **Card border-radius**: 16px
- **Card style**: `--bg-surface` background, 1px `--border-subtle` border, subtle shadow `0 4px 24px rgba(0,0,0,0.4)`
- **Card hover**: translateY(-2px), shadow deepens to `0 8px 32px rgba(0,0,0,0.5)`, border brightens to `rgba(255,255,255,0.1)`
- **Grid**: 12-column, max-width 1440px, centered

### Animation & Micro-interactions
- **Card entrance**: fadeIn + translateY(16px → 0), duration 600ms, easing `cubic-bezier(0.16, 1, 0.3, 1)`, stagger 80ms
- **Chart entrance**: scale(0.95 → 1) + fadeIn, duration 800ms
- **Number count-up**: 1200ms duration, easing easeOutExpo
- **Hover transitions**: all 200ms ease
- **Tab switch**: cross-fade 300ms

---

## Navigation Bar (Fixed Top, 64px height)
- Background: `--bg-surface` with `backdrop-filter: blur(12px)` and 80% opacity
- Bottom border: 1px `--border-subtle`
- Left: Logo icon (24px) + "APP Commercial Dashboard" (16px bold) + "Mar-Apr 2026" badge (13px, `--bg-elevated`, rounded 6px)
- Center: Month toggle pills — "March" | "April" | "Compare"
  - Inactive: `--text-secondary`, no background
  - Active: white text, `--accent-gradient` background, rounded 8px, padding 6px 16px
  - Transition: background 200ms ease
- Right: "Export HTML Report" button
  - Style: `--accent-gradient` background, white text, rounded 8px, padding 8px 16px
  - Icon: download icon (16px) before text
  - Hover: brightness(1.1), scale(1.02)

---

## Screen 1: Diagnostic Conclusion (Hero Section)

### Hero Conclusion Card (Full Width)
- Background: `--bg-surface` with a subtle gradient overlay `linear-gradient(135deg, rgba(59,130,246,0.05), rgba(139,92,246,0.05))`
- Top-left accent: 4px wide `--accent-primary` vertical bar
- Content:
  - Label: "DIAGNOSIS" (11px, uppercase, `--accent-primary`, letter-spacing 0.1em)
  - Headline: "April GMV down 12.9% (¥-42.5M)" (32px, bold, `--text-primary`)
  - Subline: "Primary drivers: completion rate -7pp + ARPU -8%" (16px, `--text-secondary`)
  - Below text: Segmented progress bar
    - Total width 100%, height 6px, rounded
    - Red segment: 70% width, `--danger` color
    - Green segment: 30% width, `--success` color
    - Labels below: "Negative Drivers (70%)" left, "Positive Offsets (30%)" right (12px, `--text-tertiary`)

### Metric Strip (3 cards, equal width, gap 20px)
Each card:
- Background: `--bg-surface`
- Left border: 3px solid (success=`--success`, danger=`--danger`)
- Top: Metric name (13px, `--text-secondary`, uppercase) + MoM badge (rounded 4px, padding 2px 8px)
  - Badge style: success = `rgba(16,185,129,0.15)` bg + `#10b981` text; danger = `rgba(239,68,68,0.15)` bg + `#ef4444` text
  - Badge content: arrow icon + percentage (e.g., "↓ 10.8%")
- Middle: Metric value (40px, bold, `--text-primary`, tabular nums)
  - e.g., "58.0%", "15.0%", "2.49%"
- Bottom: Absolute change (13px, `--text-tertiary`)
  - e.g., "vs March: -4.1pp", "vs March: -2.8pp", "vs March: +0.11pp"
- Card 1 (Completion Rate): left border `--danger`, badge red, glow `box-shadow: 0 0 20px var(--glow-danger)`
- Card 2 (Order Rate): left border `--danger`, badge red
- Card 3 (Lead Gen Rate): left border `--success`, badge green, glow `box-shadow: 0 0 20px var(--glow-success)`

### Conversion Change Chart (Full Width, Height 340px)
- Card title: "Conversion Rate Changes" with filter icon
- Chart type: Horizontal grouped bar chart + difference connectors
- 6 stages sorted by absolute MoM change (largest at top):
  - CTR, Click→Lead, Lead→Friend, Friend→Attend, Attend→Complete, Complete→Order
- Each stage: two bars side by side
  - March bar: `--chart-1` at 60% opacity, rounded left corners
  - April bar: `--chart-1` at 100% opacity, rounded right corners
  - Bar height: 16px, group gap: 24px
- Difference line: gray dashed line (`--text-tertiary` at 40% opacity) connecting bar ends
- Difference label: MoM value with arrow, positioned at line center
  - Red text + down arrow for negative, green text + up arrow for positive
- Row background: alternating `--bg-base` and `--bg-surface` (subtle)
- Y-axis labels: stage names (14px, `--text-primary`), right-aligned
- X-axis: percentage 0-100%, grid lines at 20% intervals (dashed, `--border-subtle`)
- Tooltip: floating card, `--bg-elevated`, rounded 12px, shadow
  - Content: Stage name | March value | April value | MoM change
- Animation: bars grow from left, 800ms, stagger 100ms per stage

### Action Priority Cards (Below chart, 2 columns, gap 20px)
- Left card: "Product & Engineering" — `--bg-surface` with left border `--accent-primary`
  - Header: tag icon + title (16px bold)
  - 2 action items, each with:
    - Priority badge: P0 = `--danger` bg white text (rounded 4px), P1 = `--warning` bg black text
    - Action title (15px, bold, `--text-primary`)
    - One-line rationale (13px, `--text-secondary`)
- Right card: "Strategy & Operations" — `--bg-surface` with left border `--success`
  - Same structure as left

---

## Screen 2: Conversion Funnel Overview

### Layout: Two columns (55% left / 45% right), gap 20px

#### Left Column: Funnel + Drill-down Flow
- Card title: "Conversion Funnel" with funnel icon

**Main Funnel (60% of card height)**
- ECharts funnel, 3 layers:
  1. Exposure UV (top, widest)
  2. Click UV (middle)
  3. Leads (bottom, narrowest)
- Layer colors (gradients):
  - Exposure: `#1e3a5f` → `#3b82f6` (dark blue to blue)
  - Click: `#312e5a` → `#8b5cf6` (dark purple to purple)
  - Leads: `#1e3a3a` → `#10b981` (dark green to green)
- Label: inside each layer, white text, shows "Stage Name + Count + Conversion Rate%"
- Toggle: "March" / "April" switch (same style as nav toggle)
  - Switching morphs the funnel layers smoothly (ECharts animation)

**Drill-down Flow (40% of card height)**
- Horizontal node-edge flow: Friend → Attend → Complete → Order
- Node style: rounded rectangle, `--bg-elevated` background, 1px `--border-subtle` border
  - Inner circle: conversion rate% (14px, bold, `--accent-primary`)
  - Below: stage name (12px, `--text-secondary`)
  - Below: count (13px, `--text-primary`)
- Node size: proportional to count (min 64px, max 96px width)
- Edge style: 2px line, `--text-tertiary`, with arrow marker
  - Edge label: conversion rate between stages (11px, `--text-secondary`)
- Active node (hover): border brightens to `--accent-primary`, glow effect

#### Right Column: Stage Conversion Comparison
- Card title: "Stage Conversion Comparison" with compare icon
- Horizontal grouped bar chart (same bar style as Screen 1)
- 6 stages in funnel order (NOT sorted):
  - CTR, Lead Rate, Friend Rate, Attend Rate, Complete Rate, Order Rate
- Bar pairs: March (faded) vs April (solid)
- MoM badge next to each bar pair: red down arrow or green up arrow + percentage
- Most deteriorated stage: entire row highlighted with `rgba(239,68,68,0.08)` background
- X-axis: percentage, Y-axis: stage names

### Diagnosis Cards (Full width, below two columns)
- 3 cards horizontal, gap 20px
- Each card: `--bg-surface`, rounded 16px
  - Top row: Stage name (16px bold, `--text-primary`) + Owner tag (rounded 4px, `--bg-elevated`, `--text-secondary`)
  - Middle row: March value → arrow → April value (20px bold) + MoM badge (16px, red/green)
  - Bottom row: Issue description (14px, `--text-secondary`) + icon (warning or check)
- Left border: 3px solid (red for bad, green for good)
- Examples:
  - "Complete Rate: 58.0% → 34.2% ↓41%" — "Course completion dropped significantly,督学 mechanism needs review"
  - "Order Rate: 15.0% → 12.5% ↓17%" — "High-value conversion weakened, pricing strategy needs optimization"

---

## Screen 3: Root Cause Drill-down

### Module 1: Resource Efficiency Matrix (Full width, height 440px) — MOST IMPORTANT
- Card title: "Resource Efficiency Matrix" with matrix icon
- ECharts scatter plot:
  - X-axis: Lead Gen Rate (%)
  - Y-axis: Revenue per Lead (¥)
  - Grid: dashed lines at median values (both axes), `--border-subtle`
- Quadrant backgrounds (markArea):
  - Top-Right (x>median, y>median): `rgba(16,185,129,0.06)` — label "Star ⭐" (14px, `--success`)
  - Bottom-Right (x>median, y<median): `rgba(245,158,11,0.06)` — label "Traffic Heavy ⚠️" (14px, `--warning`)
  - Top-Left (x<median, y>median): `rgba(59,130,246,0.06)` — label "Precision Gem 💎" (14px, `--accent-primary`)
  - Bottom-Left (x<median, y<median): `rgba(148,163,184,0.06)` — label "Observe 🔍" (14px, `--text-tertiary`)
- Scatter points:
  - Size: proportional to GMV (symbolSize function, min 12, max 40)
  - Color: by quadrant (green/yellow/blue/gray)
  - Border: 2px solid brighter version of fill color
  - Label: resource name (12px, `--text-secondary`, hideOverlap)
- Tooltip: floating card, `--bg-elevated`
  - Content: Resource name | Leads | GMV | Lead Gen Rate | Revenue/Lead | MoM
- Click interaction:
  - Selected point: scale(1.3), z-index top, border `--accent-primary`
  - Other points: opacity 0.3
  - Right panel slides in (30% width): sub-resource breakdown table
- Animation: points scatter from center, 1000ms, elastic easing

### Module 2: Resource Growth Matrix (Half width, height 380px)
- Card title: "Growth Matrix" with trend icon
- Scatter plot:
  - X-axis: Lead MoM change (%)
  - Y-axis: Order Rate MoM change (%)
  - Origin crosshair: `--text-tertiary` dashed line
- Quadrant labels (graphic text):
  - Top-Right: "Star" (green)
  - Top-Left: "Efficiency Up" (blue)
  - Bottom-Right: "Traffic Poison" (yellow)
  - Bottom-Left: "Declining" (red)
- Point size: proportional to April GMV
- Point color: by quadrant
- Tooltip: Resource name | Lead MoM | Order Rate MoM | April GMV

### Module 3: Resource Efficiency Ranking (Half width, height 380px)
- Card title: "Top 10 Resources" with sort icon
- Table style (div-based, NOT native table):
  - Header: `--bg-elevated` background, text `--text-tertiary`, 12px uppercase, padding 12px 16px
  - Row: `--bg-surface` background, bottom border 1px `--border-subtle`, padding 14px 16px, hover `--bg-elevated`
  - Row height: 52px
  - Columns: Resource | Leads | Lead Rate | Order Rate | GMV | MoM
  - MoM cell: arrow icon + value, colored (green/red), bold
  - Row background: growth = `rgba(16,185,129,0.06)`, decline = `rgba(239,68,68,0.06)`
  - Rank number: 14px bold, `--text-tertiary`, width 28px

### Module 4: Price Band Structure (1/3 width, height 340px)
- Card title: "Price Band Structure" with pie icon
- Two donut charts side by side (March vs April)
- Donut specs:
  - Inner radius: 55%, outer radius: 80%
  - Colors: `#3b82f6`, `#8b5cf6`, `#06b6d4`, `#64748b`
  - Label: `{b} {d}%` (name + percentage), 12px, `--text-secondary`
  - Center text: total leads count (18px bold)
- Between charts: change indicator
  - Arrow + pp change for each segment
  - Green up / Red down
- Legend: below charts, horizontal, 12px

### Module 5: Price Band × Category Sunburst (1/3 width, height 340px)
- Card title: "Price × Category Type" with sunburst icon
- ECharts sunburst, 2 layers:
  - Inner: price band (4 segments)
  - Outer: category type (Formal / Incubation)
- Colors:
  - Inner: varying blues/purples
  - Outer Formal: `#3b82f6` (solid)
  - Outer Incubation: `#10b981` (solid)
- Label: show on segments > 5%, `{b} {d}%`
- Tooltip: segment path + count + percentage

### Module 6: MAU by User Level (1/3 width, height 340px)
- Card title: "MAU by Level" with users icon
- Horizontal stacked bar chart
- Y-axis: month (March / April)
- X-axis: MAU count
- Segments: user levels, each with distinct color
- Label: percentage inside segment (if wide enough) or outside
- Legend: vertical on right

---

## Screen 4: Strategy Recommendations

### Strategy Cards Grid (3 columns, gap 20px)
Each card:
- Background: `--bg-surface`, rounded 16px, padding 24px
- Top: Strategy category tag (rounded 4px, padding 4px 10px, 12px bold)
  - "Product" = `--accent-primary` bg at 15% opacity + `--accent-primary` text
  - "Operations" = `--success` bg at 15% opacity + `--success` text
  - "Content" = `--warning` bg at 15% opacity + `--warning` text
- Title: 18px bold, `--text-primary`
- Description: 14px, `--text-secondary`, line-height 1.6
- Impact estimate: bottom of card, 13px
  - "Expected GMV impact: +¥X M" with `--success` color
  - "Risk: Medium" with `--warning` color
- Progress indicator: thin bar at bottom of card
  - Implementation difficulty: 1-5 dots (filled = `--accent-primary`, empty = `--border-subtle`)

### Resource Allocation Recommendation (Full width)
- Card title: "Resource Allocation Recommendations"
- Table:
  - Columns: Resource | Current Allocation | Recommended Allocation | Expected ROI | Confidence
  - Recommended: highlight changes with `--accent-primary` background on cell
  - ROI: green for positive, red for negative
  - Confidence: 1-5 star rating

---

## Global Interactions

### Month Toggle
- All charts, KPIs, and tables update instantly when switching months
- Transition: cross-fade 300ms for charts, count-up animation for numbers

### Hover States
- Cards: translateY(-2px), shadow deepen, border brighten
- Table rows: `--bg-elevated` background
- Chart elements: scale(1.05), tooltip appears

### Scroll Behavior
- Smooth scroll between sections
- Nav bar highlights current section (IntersectionObserver)

### Export Mode
- Click "Export HTML Report" triggers:
  1. All interactive elements disabled
  2. Charts rendered as static images (or SVG preserved)
  3. Download self-contained HTML file

---

## Key Visual Rules (DO NOT violate)
1. **NO pure black** (`#000`) anywhere. Use `#0a0a0f` for backgrounds.
2. **NO decorative colors**. Only use colors from the palette above.
3. **NO heavy borders**. Use subtle glows and background contrasts to separate elements.
4. **NO default ECharts styling**. Every chart must have custom colors, grid lines, tooltips matching the dark theme.
5. **NO cluttered tables**. Use row hover, alternating backgrounds, and generous padding.
6. **NO missing animations**. Every card and chart must have an entrance animation.
7. **NO light mode by default**. Dark mode is the primary experience.

---

## Deliverables
Generate a high-fidelity single-page dashboard mockup in dark mode with:
1. All 4 screens visible as a continuous scroll
2. At least 12 distinct chart/visualization modules
3. Interactive month toggle (visual state only)
4. Hover states on cards and chart elements
5. Consistent dark theme throughout
6. Typography using Inter + Noto Sans SC
