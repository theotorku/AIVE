# Demo Videos — LinkedIn & Facebook

Built 2026-07-10 from `demo/video/aive-e2e-demo.webm` (live dallasheatingac.com
E2E run) + brand cards matching the sales deck (navy/ice/accent). Both are
**caption-driven and muted-autoplay optimized** — no audio track. The
ElevenLabs voiceover (`demo/voiceover_script.md`) can be added later for a
sound-on variant.

## Files

| File | Platform | Spec | Structure |
|---|---|---|---|
| `aive_demo_linkedin.mp4` | LinkedIn feed | 1920×1080 (16:9), 32.4s, H.264, 1.7 MB | Hook card (3s) → captioned live demo (20.4s) → benchmark proof card (4s) → CTA card (5s) |
| `aive_demo_facebook.mp4` | Facebook feed/ads | 1080×1080 (1:1), 22.8s, H.264, 0.7 MB | Hook card (2.5s) → demo w/ headline+caption bands; middle 2.5× speed (13.3s) → proof card (3s) → CTA card (4s) |

Narrative beats (both): does AI say your name? → URL in → audit crawls/scores →
**D grade reveal, biggest gap: AI Recommendation** → 50+ HVAC benchmark, avg C →
free grade CTA. No ranking promises anywhere (offer.md rule).

## Post copy

### LinkedIn (organic)

> We graded a real Dallas HVAC company's website on AI visibility. It scored a **D**.
>
> Not because the site is bad — because AI reads websites differently than
> people do. No clear service-area statements. Thin FAQs. No structured data.
> So when a homeowner asks ChatGPT "who should I call for AC repair near me,"
> the assistant recommends the competitor it *can* read.
>
> We've now audited 50+ HVAC sites. Average grade: C. Nearly 1 in 3 are
> effectively invisible to AI.
>
> 20-second demo below. Your grade is free — link in comments.

*(Link in first comment. Tags: #HVAC #AIVisibility #LocalBusiness — max 3.)*

### Facebook (organic / groups)

> Ever asked ChatGPT to recommend a contractor? Your customers have.
> We graded a real HVAC company's website on whether AI can actually read it —
> it scored a D. Watch what the audit sees in 20 seconds. 👇
> Your website's grade is free (60 seconds): {{link}}

*(Group version: post the video with "drop your site in the comments and I'll
reply with your grade" — see gtm/11 grade-thread play.)*

### Facebook (paid ad)

- Primary text: "Most HVAC websites score a C or worse on AI visibility. When
  homeowners ask ChatGPT who to call, AI recommends the sites it can read.
  Get your grade free — takes 60 seconds."
- Headline: "What's your AI Visibility Grade?" · CTA button: Learn More

## Rebuild notes

Source pipeline (ffmpeg + PIL cards) in session scratch; brand palette
NAVY #1E2761 / ICE #CADCFC / ACCENT #3D5AFE, Liberation Sans Bold captions.
Demo footage trimmed to start at t=3s (page paint). To produce a sound-on cut:
generate VO per `demo/voiceover_script.md`, offset +3s for the hook card, and
mux with `-c:v copy -c:a aac`.
