---
name: Kinetic Precision
colors:
  surface: '#0e1512'
  surface-dim: '#0e1512'
  surface-bright: '#333b37'
  surface-container-lowest: '#09100c'
  surface-container-low: '#161d1a'
  surface-container: '#1a211e'
  surface-container-high: '#242c28'
  surface-container-highest: '#2f3632'
  on-surface: '#dde4de'
  on-surface-variant: '#bbcac1'
  inverse-surface: '#dde4de'
  inverse-on-surface: '#2b322e'
  outline: '#85948c'
  outline-variant: '#3c4a43'
  surface-tint: '#44deac'
  primary: '#44deac'
  on-primary: '#003828'
  primary-container: '#00c090'
  on-primary-container: '#004733'
  inverse-primary: '#006c4f'
  secondary: '#c0c6dd'
  on-secondary: '#2a3042'
  secondary-container: '#404659'
  on-secondary-container: '#afb4cb'
  tertiary: '#c4c6cf'
  on-tertiary: '#2d3037'
  tertiary-container: '#a7a9b2'
  on-tertiary-container: '#3b3e45'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#67fcc7'
  primary-fixed-dim: '#44deac'
  on-primary-fixed: '#002116'
  on-primary-fixed-variant: '#00513b'
  secondary-fixed: '#dce2f9'
  secondary-fixed-dim: '#c0c6dd'
  on-secondary-fixed: '#151b2c'
  on-secondary-fixed-variant: '#404659'
  tertiary-fixed: '#e0e2eb'
  tertiary-fixed-dim: '#c4c6cf'
  on-tertiary-fixed: '#191c22'
  on-tertiary-fixed-variant: '#44474e'
  background: '#0e1512'
  on-background: '#dde4de'
  surface-variant: '#2f3632'
typography:
  display:
    fontFamily: Outfit
    fontSize: 48px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '500'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '500'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: '1.4'
    letterSpacing: -0.01em
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.06em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  container-max: 1440px
  gutter: 24px
---

## Brand & Style

This design system is built for a high-stakes fintech intelligence environment where clarity and speed are paramount. The brand personality is clinical, sophisticated, and forward-leaning. It avoids the clutter of traditional enterprise dashboards in favor of a "dimmed" aesthetic that allows critical data to emerge from the shadows.

The visual style combines **Ultra-Minimalism** with subtle **Glassmorphism**. By using high-contrast typography against a deep graphite void, we create a focused "cockpit" experience. The emotional response should be one of calm control, professional authority, and technical superiority.

- **Negative Space:** Use aggressive whitespace to separate logical modules rather than heavy containers.
- **Visual Tension:** Achieve balance through precise alignment and thin, sub-pixel strokes.
- **Focus:** Primary focus is directed toward actionable intelligence via muted teal accents and soft glowing states.

## Colors

The palette is anchored by a premium dark slate base to minimize eye strain during long analytical sessions. 

- **Base Layer:** `#080b11` is the absolute background.
- **Surface Layer:** `rgba(22, 28, 45, 0.4)` provides the semi-translucent foundation for floating modules.
- **Action Emerald:** `#00c090` is reserved for primary buttons, success states, and positive market movement.
- **Status Indicators:** Use `#f59e0b` (Amber) for warnings/pending states and `#ef4444` (Crimson) for critical alerts or negative trends.
- **Borders:** Sub-pixel strokes at 5% white opacity define boundaries without adding visual weight.

## Typography

This design system utilizes a tiered typographic approach to separate high-level brand messaging from granular data analysis.

1.  **Outfit (Headers):** Used for page titles and module headers. Its geometric precision conveys a premium, modern feel.
2.  **Inter (UI/Body):** Used for all functional UI elements, descriptions, and standard data grids. It provides maximum legibility at small sizes.
3.  **JetBrains Mono (Technical):** Dedicated to transaction hashes, API keys, and raw numerical values. This ensures characters are distinct and aligns with the "intelligence engine" theme.

**Formatting Note:** Use `label-caps` for table headers and section overlines to create a clear structural hierarchy without using large fonts.

## Layout & Spacing

The layout philosophy follows a **Fluid Content / Fixed Grid** hybrid. We use a 12-column grid for desktop views with generous 24px gutters to allow the data to "breathe."

- **Desktop (1200px+):** 12 columns, 40px margins.
- **Tablet (768px - 1199px):** 8 columns, 24px margins.
- **Mobile (Up to 767px):** 4 columns, 16px margins.

Spacing should be applied in increments of 4px. Use `xl` (40px) for separating major functional blocks and `md` (16px) for internal module padding. Horizontal rules should be avoided; use vertical alignment and white space to define content groups.

## Elevation & Depth

Elevation is achieved through **Tonal Layering** and **Backdrop Blurs** rather than traditional drop shadows.

1.  **Floor:** The background (`#080b11`) is the lowest level.
2.  **Surface:** Floating modules use the semi-translucent `surface_glass` color with a `backdrop-filter: blur(12px)`.
3.  **Edge:** Every surface must have a `1px` solid border using `border_subtle`.
4.  **Luminescence:** Active states (hovered cards or selected buttons) should utilize a very soft outer glow (`box-shadow: 0 0 20px rgba(0, 192, 144, 0.15)`) to simulate a high-tech illuminated display.

## Shapes

The design system uses a **Soft** (0.25rem) radius for standard UI components. This creates a precise, architectural feel that is more sophisticated than hyper-rounded "consumer" apps but more approachable than sharp 90-degree "legacy" software.

- **Base Radius:** 4px (Buttons, Inputs).
- **Large Radius:** 8px (Cards, Modals).
- **Interactive Elements:** Maintain consistent 4px rounding to ensure they feel like part of a unified toolset.

## Components

### Buttons
- **Primary:** Background `#00c090`, Text `#080b11`, Weight 600. No shadow.
- **Ghost (Secondary):** No background, border `border_subtle`, Text `white`. Hover state adds `surface_glass`.
- **Tertiary/Ghost:** Text `#00c090`. No border or background.

### Input Fields
- **Default:** Background `rgba(255, 255, 255, 0.03)`, Border `border_subtle`.
- **Focus:** Border `#00c090`, soft inner glow. Font: Inter (14px).

### Cards / Modules
- Use the glassmorphism style defined in the Elevation section.
- **Header:** Integrate a `data-mono` label in the top-left to categorize the intelligence module.
- **Padding:** Minimum 24px internal padding.

### Data Grids
- No vertical lines.
- Horizontal lines should be `border_subtle`.
- Row Hover: Background `rgba(255, 255, 255, 0.02)`.
- Numbers should use `JetBrains Mono` for tabular lining (ensuring columns of numbers align perfectly).

### Status Chips
- Small, pill-shaped.
- Background: 10% opacity of the status color (e.g., Crimson).
- Text: 100% opacity of the status color.
- Border: 20% opacity of the status color.