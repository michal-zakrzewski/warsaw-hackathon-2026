```markdown
# Design System Strategy: The Guided Premium Assistant

## 1. Overview & Creative North Star: "The Digital Concierge"
This design system moves away from the dense, spreadsheet-heavy aesthetic of traditional finance and toward **The Digital Concierge**. The Creative North Star is a high-end, editorial experience that feels guided, calm, and authoritative. 

We break the "template" look by rejecting the rigid 1px-border grid. Instead, we use **Intentional Asymmetry** and **Tonal Depth**. By placing high-contrast `display-lg` typography against expansive `surface` areas, we create a rhythmic flow that directs the user’s eye to business value first, and data second. The interface shouldn't feel like a tool; it should feel like a premium consultation.

---

## 2. Colors & Surface Philosophy
The palette balances the growth-oriented energy of Emerald (`primary`) with the stable, institutional trust of Navy (`tertiary`).

### The "No-Line" Rule
**Strict Mandate:** Designers are prohibited from using 1px solid borders for sectioning. 
*   **The Strategy:** Define boundaries through background color shifts. A `surface-container-low` section sitting on a `surface` background creates a clear but soft structural break.
*   **The "Glass & Gradient" Rule:** To move beyond a "flat" SaaS look, use semi-transparent `surface-container-lowest` with a `backdrop-blur` (Glassmorphism) for floating navigation or sticky headers. 
*   **Signature Textures:** For primary CTAs, do not use flat hex codes. Apply a subtle linear gradient from `primary` (#006948) to `primary_container` (#00855d) at a 135-degree angle to provide "soul" and depth.

### Surface Hierarchy & Nesting
Treat the UI as a series of stacked, fine paper sheets.
*   **Level 0 (Base):** `surface` (#f7f9fb) – The canvas.
*   **Level 1 (Sections):** `surface-container-low` (#f2f4f6) – For large grouping areas.
*   **Level 2 (Priority Cards):** `surface-container-lowest` (#ffffff) – For the main interactive content.
*   **Level 3 (Pop-overs):** `surface-bright` with 80% opacity and blur.

---

## 3. Typography: Editorial Authority
We use **Manrope** exclusively. Its geometric yet humanist qualities allow it to scale from aggressive display sizes to micro-labels without losing legibility.

*   **Display & Headlines:** Use `display-md` or `headline-lg` for key financial insights (e.g., "Your Net Position"). Use `on_surface` for maximum contrast. The generous scale conveys confidence.
*   **Body & Labels:** Use `body-md` for standard text. For metadata or "secondary" information, use `label-md` with the `on_surface_variant` (#3d4a42) token.
*   **Hierarchy Tip:** Never bold everything. Use size (`display` vs `title`) and color (`on_surface` vs `on_surface_variant`) to create a clear "read-next" path.

---

## 4. Elevation & Depth: Tonal Layering
Traditional drop shadows are often messy. We use **Tonal Layering** to define hierarchy.

*   **The Layering Principle:** Place a `surface-container-lowest` (pure white) card on a `surface-container-low` (pale grey) background. This creates a "soft lift" that feels architectural rather than digital.
*   **Ambient Shadows:** If a floating element (like a modal) requires a shadow, use a blur value of `32px` or higher at 4-6% opacity. The shadow color must be tinted with `on_surface` to keep it grounded in the environment.
*   **The "Ghost Border" Fallback:** If a border is required for accessibility in input fields, use `outline_variant` at **20% opacity**. Never use a 100% opaque border.

---

## 5. Component Guidelines

### Buttons (The Interaction Pillars)
*   **Primary:** Gradient from `primary` to `primary_container`. Text: `on_primary`. Shape: `xl` (1.5rem) or `full`.
*   **Secondary:** `secondary_container` background with `on_secondary_container` text. No border.
*   **Tertiary:** Ghost style. No background, `primary` text. Use for low-priority "Cancel" or "Back" actions.

### Cards (The Information Units)
*   **Style:** Always use `rounded-xl` (1.5rem). 
*   **Constraint:** No dividers. Separate header, body, and footer using the **Spacing Scale** (e.g., `8` (2.75rem) between sections).

### Input Fields
*   **Background:** `surface_container_highest` (#e0e3e5) at 40% opacity.
*   **Focus State:** A 2px "Ghost Border" using `primary` and a subtle glow.
*   **Typography:** Labels must be `label-md` in `on_surface_variant`.

### Guided Progress (Custom Component)
*   For a "Guided Assistant," use a **Stepper Leaf**. Instead of dots or lines, use `secondary_fixed` pills that transition to `primary` when active. This reduces cognitive load by showing the "path" clearly.

---

## 6. Do's and Don'ts

### Do
*   **DO** use whitespace as a functional tool. If in doubt, increase spacing from `4` (1.4rem) to `6` (2rem).
*   **DO** use `secondary` and `tertiary` accents for non-actionable data visualization (e.g., navy bars in a chart).
*   **DO** use `rounded-xl` for all containers to maintain the "Soft Premium" feel.

### Don't
*   **DON'T** use 1px solid dividers. Use a `1px` height `surface-container-high` strip if absolutely necessary, but prefer whitespace.
*   **DON'T** use pure black (#000000) for text. Always use `on_background` or `on_surface`.
*   **DON'T** use standard "Alert Red" for warnings unless it's a critical error. Use `error_container` with `on_error_container` for a more sophisticated, less alarming notification.

---

## 7. Spacing & Rhythm
Consistency is the key to "Trustworthy" design. Use the **Spacing Scale** religiously.
*   **External Margins:** Always use `10` (3.5rem) or `12` (4rem) for page gutters.
*   **Internal Padding:** Cards should have a minimum internal padding of `6` (2rem) to allow the content to breathe.

By following these guidelines, you move from "making a demo" to "crafting an experience." Every pixel should feel like a deliberate choice by a high-end financial advisor.```