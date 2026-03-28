# Design System Strategy: The Financial Atelier

## 1. Overview & Creative North Star
This design system is built on the Creative North Star of **"The Digital Curator."** In the complex world of green finance and AI, our role is not just to display data, but to curate it with an editorial precision that feels both authoritative and breathable. 

We move beyond the "standard SaaS template" by embracing **Sophisticated Asymmetry** and **Tonal Depth**. Instead of rigid, boxed-in grids, we use expansive white space and overlapping layers to create a sense of movement and transparency. The goal is a UI that feels like a high-end financial broadsheet—serious and secure, yet light enough to feel modern and approachable.

---

## 2. Colors & Surface Architecture
Our palette transitions from clinical whites to deep, intellectual navies, punctuated by a high-growth emerald.

### The "No-Line" Rule
To achieve a premium, custom feel, **1px solid borders are prohibited for sectioning.** Structural separation must be achieved through background shifts.
- **Surface-Container-Low (`#f3f4f5`)** acts as your primary canvas.
- **Surface-Container-Lowest (`#ffffff`)** is used for interactive "hero" cards to make them pop.
- **Surface-Dim (`#d9dadb`)** defines sidebar or utility areas to create a grounding "anchor" for the eyes.

### Signature Textures: Glass & Gradients
Flat colors are for utilities; "Moments of Truth" (CTAs and high-level AI insights) require soul.
- **The Emerald Gradient:** For primary actions, transition from `primary` (`#00513c`) to `primary_container` (`#006b51`) at a 135-degree angle. This adds a subtle, gem-like depth.
- **The Navy Anchor:** Use `tertiary` (`#00468b`) for high-level navigation and data headers to signal enterprise-grade security.

---

## 3. Typography: Editorial Authority
We utilize a dual-typeface system to balance technical precision with human approachability.

*   **Display & Headlines (Manrope):** We use Manrope for all titles. Its geometric yet slightly soft curves provide a "modern-humanist" feel. Use `headline-lg` (2rem) with tight letter-spacing (-0.02em) to create an authoritative, editorial look.
*   **Body & UI (Inter):** Inter is our workhorse. It is engineered for readability in data-heavy environments.
*   **The Hierarchy Shift:** Always pair a `headline-sm` in `on_surface` with a `label-md` in `on_surface_variant` to create a clear "Title/Caption" relationship that guides the user’s eye without requiring lines.

---

## 4. Elevation & Depth: Tonal Layering
Traditional drop shadows are often messy. We use **Tonal Layering** and **Ambient Light** to convey hierarchy.

*   **The Layering Principle:** Place a `surface_container_lowest` (#ffffff) card on top of a `surface_container` (#edeeef) background. This creates a natural 0.5rem "lift" without a single pixel of shadow.
*   **Ambient Shadows:** For floating elements (Modals/Popovers), use an ultra-diffused shadow: `0px 24px 48px -12px rgba(25, 28, 29, 0.08)`. Note the use of `on_surface` as the shadow tint rather than pure black.
*   **The Ghost Border Fallback:** If a border is required for accessibility in forms, use `outline_variant` (#bec9c3) at **20% opacity**. It should feel felt, not seen.
*   **Glassmorphism:** For top navigation bars, use `surface` (#f8f9fa) at 80% opacity with a `20px backdrop-blur`. This allows the "green finance" data to bleed through subtly as the user scrolls.

---

## 5. Components

### Cards & Lists
*   **The Rule of Radii:** All main cards must use `xl` (1.5rem/24px) or `lg` (1rem/16px) corner radii.
*   **No Dividers:** Lists should be separated by a `spacing-2` (0.7rem) gap or a subtle shift from `surface` to `surface_container_low`. Never use a horizontal rule.

### Buttons
*   **Primary:** Gradient of `primary` to `primary_container`. White text. Rounded `full` (9999px) for a "pill" look that feels approachable.
*   **Secondary:** `secondary_container` (#bdd6ff) background with `on_secondary_container` (#445d80) text.
*   **Tertiary:** No background. `primary` text. Use for low-priority actions like "Cancel" or "Learn More."

### Input Fields
*   **Surface:** Use `surface_container_highest` (#e1e3e4). 
*   **State:** On focus, transition the background to `surface_container_lowest` (#ffffff) and add a `2px` "Ghost Border" of `primary`.

### AI Insight Chips
*   **Style:** Semi-transparent `primary_fixed_dim` (#71d9b4) with a `surface_tint` (#006c52) icon. These should appear "illuminated" to signify AI-generated content.

---

## 6. Do’s and Don’ts

### Do:
*   **Do use asymmetric padding.** For example, give a hero section `spacing-16` on the top and `spacing-10` on the bottom to create a "pushed" editorial look.
*   **Do lean on color for status.** Use `error` (#ba1a1a) sparingly; for financial "warnings" that aren't critical, prefer `secondary` navies to maintain a "calm" dashboard environment.
*   **Do use whitespace as a separator.** Use the `spacing-6` (2rem) token between logical data groups.

### Don’t:
*   **Don't use pure black (#000000).** Always use `on_surface` (#191c1d) for text to keep the contrast high-end rather than harsh.
*   **Don't use 1px dividers.** If you feel the need for a line, try a `4px` vertical accent of `primary_fixed` in the margin instead.
*   **Don't crowd the charts.** Data visualizations should have at least `spacing-8` of "breathing room" on all sides to remain interpretable.