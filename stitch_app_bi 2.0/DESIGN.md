---
name: Precision Analytics
colors:
  surface: '#f7f9fc'
  surface-dim: '#d8dadd'
  surface-bright: '#f7f9fc'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f7'
  surface-container: '#eceef1'
  surface-container-high: '#e6e8eb'
  surface-container-highest: '#e0e3e6'
  on-surface: '#191c1e'
  on-surface-variant: '#434655'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f4'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0053db'
  primary: '#004ac6'
  on-primary: '#ffffff'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#b4c5ff'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#943700'
  on-tertiary: '#ffffff'
  tertiary-container: '#bc4800'
  on-tertiary-container: '#ffede6'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffdbcd'
  tertiary-fixed-dim: '#ffb596'
  on-tertiary-fixed: '#360f00'
  on-tertiary-fixed-variant: '#7d2d00'
  background: '#f7f9fc'
  on-background: '#191c1e'
  surface-variant: '#e0e3e6'
typography:
  h1:
    fontFamily: Noto Sans SC
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
  metric-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  metric-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-main:
    fontFamily: Noto Sans SC
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  helper:
    fontFamily: Noto Sans SC
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  container-padding: 24px
  gutter: 16px
  card-gap: 20px
  element-tight: 8px
  element-loose: 16px
---

## Brand & Style

This design system is engineered for the high-density information requirements of APP lead advertising platforms. The brand personality is rooted in **Modern Corporate** aesthetics—prioritizing reliability, analytical precision, and clarity. 

The visual narrative focuses on "Data Transparency," utilizing a systematic approach to whitespace and structural alignment to reduce cognitive load for performance marketers. The emotional response is one of confidence and control, achieved through a refined "Light Grey-Blue" canvas that makes vibrant data visualizations pop without causing eye fatigue during long sessions.

## Colors

The palette is anchored by "Data Blue," a high-visibility primary color used for interactive elements and primary data series. The system employs a "Signal-to-Noise" approach: 
- **Functional Backgrounds:** Use #F5F7FA to create a distinct depth between the application chrome and the content workspace.
- **Semantic Feedback:** Success and Danger colors are reserved strictly for performance delta (growth/decline) and system status alerts.
- **Categorical Charts:** A distinct 6-color sequence ensures high contrast in multi-line charts and complex pie distributions, maintaining accessibility and rapid recognition.

## Typography

The typography system pairs **Noto Sans SC** for its exceptional multi-language legibility with **Inter** for UI labels and metrics to give the dashboard a modern, utilitarian edge. 

Information hierarchy is established through weight and color rather than excessive size shifts. **Metrics** must always use Medium (500) or Bold (700) weights to ensure data points are the first thing a user sees. Labels use a slightly muted #4B5563 to stay secondary to the actual data values.

## Layout & Spacing

The layout utilizes a **12-column fluid grid** system optimized for desktop viewing. To maintain a "Precise Data" look, the system follows a 4px baseline grid.

- **Margins:** Standard page margins are set to 24px.
- **Gutters:** Standard 16px gutters provide breathing room between widgets without fragmenting the screen.
- **Density:** High-density lists and tables use 8px vertical padding to maximize visible information per scroll.

## Elevation & Depth

This design system uses **Tonal Layers** combined with **Low-Contrast Outlines** to define space. 

1.  **Level 0 (Base):** The #F5F7FA background acts as the canvas.
2.  **Level 1 (Cards):** White (#FFFFFF) surfaces with a 1px #E8E8E8 border. A subtle, soft shadow (Y: 2px, Blur: 4px, Color: rgba(0,0,0, 0.04)) is applied to provide a "lifted" feel from the base.
3.  **Level 2 (Popovers/Modals):** These use a more pronounced shadow (Y: 10px, Blur: 20px, Color: rgba(0,0,0, 0.08)) to indicate temporary interaction layers.

Interactive elements like buttons do not use heavy shadows, relying on flat color fills to indicate state.

## Shapes

To maintain a professional B-end aesthetic, the system uses a **Soft (0.25rem/4px)** base radius for small components (inputs, buttons) and a **Large (0.5rem/8px)** radius for major containers and cards. 

This specific balance ensures the UI feels approachable but retains the structural "tightness" expected of a financial or analytical tool. Avoid pill-shaped buttons unless used for specific "New/Create" primary actions to differentiate them from standard utility buttons.

## Components

### Buttons & Controls
- **Primary:** Solid #2563EB with white text. 4px border-radius.
- **Secondary:** White background with 1px #E8E8E8 border and #4B5563 text.
- **Ghost:** No border or background, using #2563EB text for low-priority actions.

### Cards
- Standard data containers must include a 16px internal padding.
- Card headers should have a 1px #E8E8E8 bottom border when title and actions are present.

### Form Inputs
- **Default State:** 1px #E8E8E8 border with #FFFFFF background.
- **Focus State:** 1px #2563EB border with a 2px soft blue outer glow.
- **Labels:** Always placed above the input in #4B5563 (Label-caps style).

### Data Visualization
- **Line Charts:** Use a 2px stroke width. Points should only appear on hover.
- **Tables:** Zebra-striping is discouraged; use 1px #F3F4F6 bottom borders for row separation instead.
- **Status Chips:** Small badges with a light background tint of the semantic color (e.g., light green background with #10B981 text) to indicate status without overpowering the data.