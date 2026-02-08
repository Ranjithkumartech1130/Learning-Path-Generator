# UI Design System Update
**Date:** 2024-05-23
**Theme:** Modern Educational (Soft & Professional)

## Color Palette
The new design system focuses on a clean, modern, and student-friendly aesthetic with soft gradients and high readability.

### Color Swatches
- **Dark Navy (Backgrounds):** `#5A5564`
- **Teal (Primary/Interactive):** `#78B8B8`
- **Pink (Highlights):** `#D89F9E`
- **Wine (Secondary Accents):** `#906C7D`
- **Blue (Surfaces/Borders):** `#7287AB`

### Backgrounds
- **Body Background:** Soft Educational Gradient
  - Colors: `#5A5564` → `#656070` → `#7287AB`
  - Animation: 20s infinite ease loop (Calm movement)
- **Cards (Glassmorphism):**
  - Background: `rgba(90, 85, 100, 0.85)`
  - Border: `rgba(114, 135, 171, 0.3)`

## Component Updates

### 1. Typography
- **Headings:** Font 'Outfit', with gradient text fills (Teal → White → Pink) and soft teal drop-shadows.
- **Body:** Font 'Inter', color `#d1d5db` (Light Grey).

### 2. Buttons
- **Primary Button:**
  - Gradient: Linear (135deg, Teal `#78B8B8` → Darker Teal `#609da0`)
  - Hover: Lift and glow.

### 3. Interactive Elements
- **Forms:** Inputs have a dark navy/purple wash.
- **Navigation Tabs:** Pill-shaped, using Primary to Blue gradients.

- **Task List:** Active tasks highlighted with a Teal tint and left border indicator.

### 4. Animations
- **Title Glow:** Pulsing shadow effect on the main hero title.
- **Border Flow:** Animated gradient border on the Hero Card.
- **Background Movement:** Slow, subtle shift of the background gradient for a "living" feel.

## Files Modified
- `backend/public/style.css` - Core design system and component styles.
- `backend/public/index.html` - Inline style updates for specific elements (Back to Top button).
- `backend/public/script.js` - Color updates for dynamic JS-generated elements.
- `backend/public/template-styles.css` - Resume template alignment.
