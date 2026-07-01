# LEARNINGS

Append-only log of what worked and what got rejected on past builds. Read this before designing (Step 0); add to it after delivering (Step 5). Newest entries at the bottom. Keep each entry short.

Format:
```
## YYYY-MM-DD — <subject>
- Built: <what>
- Accepted: <what the user kept / liked>
- Changed/Rejected: <what they pushed back on>
- Pattern: <reusable lesson>
```

---

## 2026-06 — Barbershop (FORM), Calgary — seed entry
- Built: single-file 3D landing page. Signature = rotating 3D barber pole (climbing stripes, cursor tilt, scroll drift). Dark leather/brass palette (#14110F / #C9A35B / #7A2E2A / #EDE6D8), Fraunces + Archivo type. Later added a floating-reviews marquee (two rows, opposite directions, pause-on-hover, edge fades) between the About and Services sections.
- Accepted: the barber-pole signature over a coded human; single self-contained HTML over Next.js; conversion-first layout (book CTA above fold, click-to-call, hours, services-with-prices menu); reviews as a two-row auto-scrolling marquee.
- Changed/Rejected: the original brief's "3D photorealistic guy with a crew cut" hero — not buildable from code without a model file; replaced with the barber pole. Next.js + Tailwind stack — dropped in favor of a double-click file because the user doesn't code.
- Pattern:
  - For a local service business, argue for conversion over spectacle every time; 3D belongs as an accent.
  - Never accept a "photorealistic 3D person" hero from code alone — propose a subject-appropriate object instead.
  - Default to a single self-contained HTML file for non-coders; only use a framework on explicit request.
  - Marquee loops need an exact duplicate set for a seamless seam, and the speed is fixed in seconds — adding/removing cards unevens it, so re-tune duration to card count.
  - Flag invented reviews as placeholders to swap for real ones (FTC + reputation risk).
