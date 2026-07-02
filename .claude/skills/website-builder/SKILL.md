---
name: website-builder
description: Build a complete, self-contained website in a single HTML file — high-end 3D and animated landing pages using Three.js and GSAP, mobile-first and conversion-focused. Use this skill whenever the user types /website-builder, /wb, or asks to build, design, or generate a website, landing page, one-pager, marketing site, or 3D/immersive/animated web experience — including for a local business like a barbershop, salon, gym, cafe, or any service shop — even if they never say the word "skill". Also use it when iterating on a site built earlier (adding sections, restyling, fixing responsiveness or performance). The skill reads its own LEARNINGS.md first to apply past preferences, and appends new lessons at the end so each build improves. Do not use it for backend code, data pipelines, or non-web deliverables.
---

# Website Builder

Build websites the way a small studio's design lead would: opinionated, subject-specific, and never templated — but with the honesty of a technical peer who will tell the user when the brief works against their own goal.

Two jobs, always in this order: **(1) make sure we're building the right thing, then (2) build it beautifully.**

---

## Step 0 — Read your own learnings first

Before designing anything, open `LEARNINGS.md` in this skill folder and read it. It holds patterns that were accepted or rejected on past builds. Apply the accepted ones, avoid the rejected ones. This is what makes the skill improve over time — treat it as the memory the file format can't give you on its own. (See "Step 5" for how it gets updated and when it actually persists.)

---

## Step 1 — Challenge the brief before you build it

The user's brief is a starting point, not orders. Pressure-test it out loud, briefly, before writing code:

- **Does the visual ambition fight the business goal?** A heavy 3D/WebGL site is an agency-portfolio move. For a *local service business* (barbershop, salon, gym, dentist), the site's job is bookings, and heavy 3D hurts the exact things that win: mobile performance, Core Web Vitals, and a fast path to "Book Now." Flag this. Recommend 3D as a restrained *accent*, not the architecture, unless the site's real purpose is spectacle (a portfolio or a demo meant to impress).
- **Is any part not buildable from code alone?** The classic trap: "a 3D photorealistic person." Three.js gives geometry and shaders, not human heads — that needs a pre-made GLTF/GLB model (Blender or a scan). Never fake it with a low-poly blob; say so and propose a subject-appropriate object instead (a barber pole for a barbershop, a spinning record for a music shop, etc.).
- **State assumptions inline** rather than blocking. Only ask a question when the answer genuinely changes the build. The usual fork worth asking: *is this a client/business deliverable (optimize for conversion) or a portfolio/flex piece (optimize for spectacle)?*

Keep this to a few sharp sentences. Don't lecture, don't pad, then move on.

---

## Step 2 — Design plan (do this in your head, show only the summary)

Follow the frontend-design discipline. Produce a compact token system tied to *this* subject:

- **Palette:** 4–6 named hex values drawn from the subject's real materials (leather/brass/oxblood for a traditional barbershop; not a generic scheme).
- **Type:** a characterful display face + a complementary body face (+ a utility face for labels/data). Pair deliberately — not Playfair + Inter, not the same combo you'd reach for on any project.
- **Layout:** one-sentence concept + rough mental wireframe.
- **Signature:** the single element the page is remembered by. Spend your boldness here and keep everything else quiet.

**Avoid the three AI defaults** — cream + high-contrast serif + terracotta; near-black + one acid accent; broadsheet hairline-rule columns. If your plan drifts into one of these without the brief asking for it, change it.

---

## Step 3 — Build (technical defaults)

**Output one self-contained `index.html`** unless the user explicitly asks for a framework/build step. Reasoning: most users — especially non-coders — just want to double-click a file and see it. A Next.js monorepo is a worse deliverable for them, not a better one. Only reach for React/Next/Tailwind-config when the user asks or the project genuinely needs it.

Stack, loaded via CDN classic `script` tags (works on double-click, no build):
- Three.js r128 (global `THREE`) for the 3D signature.
- GSAP 3 + ScrollTrigger for scroll reveals and parallax.

**Section structure** (the standard high-end landing layout):
1. **Sticky minimal nav** — transparent over hero, gains a blurred background on scroll.
2. **Hero** — full viewport (`100svh`). The signature 3D element dominates the background; bold display headline + primary CTA over a vignette that keeps text legible. Cursor parallax/tilt on the 3D. Secondary CTA = click-to-call for local businesses.
3. **About / story** — text reveals on scroll; 3D subtly drifts or fades.
4. **Features / services / portfolio** — grid of cards that tilt in 3D on hover with an ambient glow that follows the cursor.
5. **Footer CTA** — final bold call to action over an animated background; hours, location, click-to-call.

**Conversion essentials for any business site** (bookings over spectacle): primary CTA above the fold, click-to-call, hours, location, and social proof. Wire the booking button to the user's real booking URL/embed — leave an obvious placeholder if unknown.

**Performance floor:** cap `renderer.setPixelRatio` at 2, pause the render loop when the tab is hidden, keep geometry low-poly. Don't promise "60fps" blindly — say it's built light and should be tested on a real mid-range phone.

**Accessibility floor (non-negotiable):**
- `prefers-reduced-motion`: stop the 3D animation, marquees, particles, and card tilt; reveal all content immediately; freeze any noise/grain.
- Visible keyboard focus (`:focus-visible` outline in the accent color).
- Semantic HTML, responsive down to ~320px.

**Copy is design material.** Write real, specific, end-user-facing copy — never lorem ipsum, never AI filler ("elevate your experience"). Mark placeholders clearly (brand name, phone, address, booking URL).

**Never ship fabricated social proof as if real.** Invented testimonials/ratings on a live business site are an FTC problem and a reputation risk. Use clearly-placeholder reviews and tell the user to replace them with real ones before launch.

For the concrete, reusable code patterns — 3D signature object, GSAP reveals, card tilt+glow, floating-review marquee, animated grain, reduced-motion handling — read `references/build-recipe.md`.

**If the subject is a barbershop or another personal-service local business** (salon, spa, gym, tattoo studio, med-spa) — also read `references/barbershop-personal-service-recipe.md` before building. It covers the section-by-section content architecture (services, gallery, team, booking) and the booking-flow conversion pattern for this category, including an honest note on what a static single-file build can and can't actually do for booking/email (don't let a confirmation-screen mockup get presented to the user as a working booking system).

---

## Step 4 — Self-critique before delivering

Look at it with fresh eyes and **remove one accessory** (Chanel's rule). Confirm: reduced-motion works, keyboard focus is visible, it holds up on mobile, and the signature is the *one* bold thing rather than five competing effects. Deliver the file (save to the outputs directory and present it) with a short setup note and the swap-in placeholders called out.

---

## Step 5 — Learn from this build (update LEARNINGS.md)

After delivering and seeing the user's reaction, append a short entry to `LEARNINGS.md`: the subject, what was built, what the user accepted / changed / rejected, and any reusable preference or pattern. Keep entries to a few lines. Over many builds this becomes a real preference memory that Step 0 feeds back in.

**Honest constraint on persistence — tell the user plainly:** this write-back only carries across future conversations if the skill folder is **writable and persistent** — i.e. running in Claude Code or Cowork against a local folder, or a skill kept in a git repo. In the claude.ai chat sandbox the filesystem resets between conversations, so the update won't survive on its own. When that's the case, either:
- output the updated `LEARNINGS.md` and tell the user to commit it back to the repo where the skill lives, or
- note that the lesson should be saved manually.

Do not imply the skill silently rewrites itself. It improves because it reads and appends a log — and only if that log is stored somewhere that lasts.

---

## The intake brief (fill this in per project)

This is the original template this skill was built from. Fill each bracket from the user's request; apply the Step 1 corrections (swap any impossible photoreal-human hero for a subject-appropriate signature object; default to a single self-contained file).

- **Subject:** what business/product is this for?
- **Theme:** the visual direction in the subject's own vernacular (e.g. "classic tradition with modern edge").
- **Signature 3D/animated element:** the one memorable object, buildable from code or a supplied model.
- **Sections:** hero, about, features/services, footer CTA (adjust to the subject).
- **Stack:** single-file HTML + Three.js + GSAP by default; framework only on request.
- **Deliverable:** complete code + a brief local-run setup guide.
