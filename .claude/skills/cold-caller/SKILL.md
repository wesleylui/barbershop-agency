---
name: cold-caller
description: Generate high-converting, word-for-word cold call scripts for B2B outreach. Use this skill immediately whenever the user types /cc, asks for a cold call script, phone sales script, outreach call script, or says they need to know what to say on a call. Also trigger when the user mentions calling a prospect, preparing for a phone call, or wants help with what to say when they call a business. This skill produces a complete script using a customer-first pattern interrupt opener, followed by a natural reveal, hook, objection handlers, and voicemail — optimised for the highest possible conversion to a booked meeting.
---

# Cold Caller

Generates a complete, high-converting cold call script based on the context provided. Output is word-for-word, ready to read from — not a framework or bullet points.

## Step 0 — Read your own learnings first

Before writing a script, open `LEARNINGS.md` in this skill folder and read it silently. Apply accepted patterns (openers, hooks, objection responses that landed) and avoid rejected ones (phrasing that got hung up on, angles that fell flat). Don't narrate this step to the user — just fold it into the script you generate.

After a real call happens, the user can run `/learn` (the `reflect` skill) to capture what worked, what didn't, and what changed — it appends the lesson to this file. This only persists if this skill folder is writable and persistent (Claude Code / Cowork / a git repo) — in the claude.ai chat sandbox, `LEARNINGS.md` must be manually recommitted each session.

## Trigger

User types `/cc` followed by context. Examples:
- `/cc calling Taza Barbershop, their booking button doesn't work on mobile`
- `/cc barbershop owner named James, 4 chairs, no website`
- `/cc med spa Calgary, owner is Sarah, not in Google map pack`

If `/cc` is typed with no context, ask for three things before writing:
1. Prospect name and business type
2. The specific booking or funnel problem identified
3. What you sell / what you fix

Never write a generic script without a specific hook.

---

## The mindset that produces the right tone

Before reading the script, understand this: you are not a salesperson on this call. You are a peer who found something wrong and is calling to tell them about it. A doctor doesn't apologize for calling you about your test results. They're direct and confident because what they found matters.

You looked at their booking page. You found a real, specific, fixable problem. You're calling to tell them about it. That's not a sales call. That's a service call. Every word in this script comes from that place — not from trying to sound helpful, but from genuinely being useful.

Never apologize for calling. Never fill silence with nervous talking. Never abandon your conviction because they seem busy. Busy people say yes to things that clearly matter to them.

---

## The emotional arc — where you're guiding them

Every call moves the prospect through five emotional states:

**Curiosity** — the customer opener. They don't know why you're calling yet. They're mildly intrigued.

**Recognition** — the reveal. You were specifically on their site. You noticed them. They feel seen, not pitched.

**Concern** — the bridge. You name the cost of the problem in plain terms. They feel the weight of bookings they're losing right now without knowing it.

**Relief** — the soft ask. You have a fix and it's not complicated. The 15-minute call is positioned as relief, not a sales presentation.

**Trust** — underneath all of it. You co-own a barbershop. You're not a vendor from outside their world. You're a peer who noticed something.

You are guiding them through this arc. Not pushing. Guiding.

---

## Tone principles — what persistent, respectful, and genuinely helpful sounds like

**Conviction over enthusiasm.** Don't sound excited about your service. Sound certain about the problem. Enthusiasm reads as sales. Certainty reads as expertise.

**Direct without being aggressive.** State what you found, state what it costs, ask for the meeting. No hedging, no softening with "I was just wondering if maybe..." but also no pressure. You're informing, not forcing.

**Acknowledge their reality.** They're running a shop. Clients are in the chair. They've heard pitches before. You can say "I know you're probably mid-shift and I'll be quick" — that acknowledgement earns more goodwill than any opener trick.

**Silence is your ally.** After the soft ask, stop. The silence belongs to them. Filling it signals you're nervous, which signals you're not sure they should say yes.

**Persistent means: every follow-up adds something new.** Persistence is not repeating yourself. It's delivering value across multiple channels across multiple days. "Just checking in" is not follow-up. It's noise. Every touch you make should give them something they didn't have before — a Loom, a screenshot, a specific number, a new angle.

**Respectful means: you don't push for a sale. You push for a meeting.** The line is there. Stay on the right side of it.

---

## The full script — nine stages

### Stage 1: Customer opener

Open as a genuine potential customer trying to book. You already know their booking flow is broken. Now you experience it live on the call.

```
YOU: "Hey, is this [shop name]?"

[They confirm]

YOU: "Hey — I was actually looking to book an appointment.
Do you guys have anywhere online I can do that?"
```

Listen. Their answer is your hook:

If "No, you'd have to call us" → no online booking. Use this word for word in the bridge.
If "Yeah it's on our website" → "I was on there actually and couldn't get it to work."
If "Yeah go to [link]" → "I tried that — it just opened a blank page, nothing was selected."

They have now confirmed the problem to you in their own words. That is worth more than anything you could say.

---

### Stage 2: The reveal

Immediately after their answer. Naturally — not robotic. Warmth here, not formality.

```
YOU: "Actually, I have to be honest with you —
my name's Matthew, I run a small marketing agency
that works with barbershops here in Calgary.
I also co-own one myself — FORM Barbershop.
I was on your site specifically because I noticed
the booking situation, and I wanted to see what it
felt like from a client's side.
Can I tell you what I found in 30 seconds?"
```

You were just a customer. Now you're a peer who cares enough to call personally. That is a completely different energy than any sales call they've ever taken.

---

### Stage 3: The bridge

This is the pitch. Three sentences. Name what they just experienced, put a cost on it, done. Do not list features. Do not explain your service. Do not go longer.

```
YOU: "So what I just experienced — [the exact thing:
blank booking page / couldn't find online booking /
site not working on mobile] — that's what every client
who finds you online is hitting right now.

Most of them just close the tab and book somewhere else.
They don't call, they don't try again — and you'd
never know because there's no notification when it happens.

For a shop your size, that's probably 5 to 10 bookings
a week just walking out the door."
```

Stop here. The pitch is done. Silence.

---

### Stage 4: Credibility bridge

One line. Already woven into the reveal, but reinforce if needed.

```
YOU: "I've been on both sides of this — I know what
a full chair looks like, and I know exactly
what's breaking your flow."
```

---

### Stage 5: The soft ask

Not "are you interested?" — binary questions get binary rejections.

```
YOU: "I'd love to jump on a 15-minute call this week,
pull up your site, and show you exactly what
the fixed version looks like for your shop.
No pitch — just the problem and the fix.
Would that make sense?"
```

Then stop. Do not fill the silence.

---

### Stage 6: Book it immediately if they say yes

Do not let momentum die.

```
YOU: "Perfect. What does [day] look like —
morning or afternoon?"

[Once they give a time]

YOU: "I'll send you a Calendly link right now
to lock it in. What's the best way to reach you?"
```

---

### Stage 7: Objection handlers — tone matters as much as words

Each response acknowledges their reality before redirecting. Never argue. Never justify. Acknowledge, then move.

**"I'm busy / bad time"**
```
YOU: "Totally fair — I know I caught you mid-day.
What's a better time, tomorrow morning or
later this week? I'll call back then."
```

**"Send me an email"**
```
YOU: "Happy to — what's the best address?
And just so I send the right thing:
the situation I hit when I tried to book just now —
was that news to you, or did you know it was happening?"
```
[This re-engages before they mentally hang up. If they didn't know, they're back. If they did know, you've shown empathy and planted a seed.]

**"Not interested"**
```
YOU: "I hear you — and I respect that.
One quick question before I let you go:
what I ran into trying to book online just now —
were you aware that was happening to your clients?"
```
[If no → they re-engage. If yes → "Okay, fair enough. If you ever want to look at it, I'm at [number]. Good luck with the shop." Clean exit. No pressure. Leaves them with a positive impression.]

**"I already have someone handling my marketing"**
```
YOU: "That makes sense — and honestly this isn't
a marketing thing. It's a technical issue with
how your booking tool is set up right now.
It's probably slipping through the cracks even if
someone's on the marketing side.
Fifteen minutes is all it takes to see it —
worth a quick look?"
```

---

### Stage 8: Voicemail

25 seconds. Specific curiosity. Don't explain everything — leave just enough to make them need to call back.

```
YOU: "Hey, this is Matthew calling for [shop name].
I was actually on your site trying to book an appointment
and ran into something specific that I think is
costing you bookings every week.
Won't go into it on a voicemail, but give me a call back
at [number] and I'll show you exactly what I mean.
Takes two minutes. Thanks."
```

---

### Stage 9: Quick reference cheat sheet

Three lines to glance at mid-call.

```
HOOK: [specific thing that's broken — fill in per prospect]
COST: "5-10 bookings a week walking out the door, you'd never know"
ASK: "15-minute call — no pitch, just the problem and the fix"
```

---

## The persistence sequence — five touches over three weeks

When they don't engage on the first call, this is the follow-up sequence. Every touch adds something new. Never just check in.

**Day 1 — The call**
Run the full script above. If no answer, leave the voicemail.

**Day 3 — Instagram DM**
Send the Loom video of their broken booking flow.
Message: "Sent you a voicemail a couple days ago — recorded a 90-second video of what I found on your site. Worth a look: [Loom link]"

**Day 7 — Email**
Subject: [Their shop name]
Body: One paragraph. Reference the specific problem. Attach a screenshot or screen recording.
"This is what someone sees when they try to book a kids cut on your site right now. Wanted to make sure you saw it. Happy to show you the fixed version on a quick call — [Calendly link]."

**Day 14 — Second call**
Shorter. You've already delivered the value.
YOU: "Hey, I sent you a few things over the last couple weeks — just wanted to make sure it didn't get buried. Did you get a chance to see the video?"

**Day 21 — Final touch**
YOU: "Hey, last message from me on this — I don't want to keep filling up your feed. If the timing's ever right to look at the booking situation, I'm at [number]. Either way, good luck with the shop."

This creates finality and often gets a response from people who meant to reply but never did. Clean, respectful, leaves a good impression whether they say yes or no.

Five touches is not harassment. It's commitment. Harassment is saying the same thing every day. What you're doing is delivering real value across multiple channels and giving them time on their terms.

---

## Adapting the opener when booking is not the issue

If the problem is visibility, adapt Stage 1:

```
YOU: "Hey, is this [shop name]?"
[They confirm]
YOU: "Hey — I was actually trying to find you on Google
to look up your hours. I searched barbershop [neighbourhood]
and you didn't come up. Is there another way to find you?"
```

Same customer frame. Different hook. Reveal and pitch stay identical.

---

## Quality bar

The script should feel like it was written by someone who:
- Actually tried the prospect's booking flow before calling
- Co-owns a barbershop and talks to owners as a peer
- Is trying to help a business they believe in fix something real
- Genuinely doesn't need this one client to say yes — confidence, not desperation

If context is thin, ask for more before writing.
