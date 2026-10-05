# Voiceover Script — `aive_demo_facebook.mp4` (ElevenLabs)

Narration matched to the **Facebook 1:1 cut** (`gtm/video/aive_demo_facebook.mp4`):
1080×1080, **22.8s**, four segments — Hook card (2.5s) → live demo, middle at
2.5× speed (13.3s) → benchmark proof card (3s) → CTA card (4s).

Brand voice: concrete, operator tone, no emoji, no hype. **Never promise
rankings or recommendations inside AI** — we sell clarity on what to fix, not
placement.

> Note: the existing `demo/voiceover_script.md` is timed to the 23.4s raw webm.
> This file is the shorter, faster VO cut for the square Facebook video.

---

## ElevenLabs production settings

- **Model:** Eleven Multilingual v2 (or v3 for the bracket emotion tags).
- **Voice:** calm, credible mid-range male or female (e.g. "Daniel", "Sarah").
  Avoid bright "ad read" voices — confident demo, not a hype reel.
- **Stability:** 50 · **Similarity:** 75 · **Style:** 0–15 · **Speaker boost:** on.
- **Speed:** 1.05 (the square cut is tighter than the webm). If your render runs
  long, nudge to 1.1; if short, the trailing CTA pause absorbs it.
- `<break time="x.xs" />` tags hold the VO to the card cuts. Remove them to
  free-run and edit to picture.

---

## Timed script (matched to 22.8s)

| Time | On screen | Line |
|---|---|---|
| 0:00–0:02.5 | Hook card ("does AI say your name?") | When a customer asks AI who to call — does it say your name? |
| 0:02.5–0:15.8 | Live demo (URL in → crawl → score → D reveal) | Drop in any business URL, and the AI Visibility Audit reads the site the way ChatGPT does — crawling every page, pulling out the services, scoring how clearly AI understands the business. This real Dallas HVAC company scores a D. Biggest gap — AI Recommendation. |
| 0:15.8–0:18.8 | Proof card (50+ HVAC, avg C) | We've audited fifty-plus HVAC sites. The average grade is a C. |
| 0:18.8–0:22.8 | CTA card (free grade) | See exactly what AI misses on your site. Your grade is free — sixty seconds. |

Word count: ~72. At 1.05 speed with the breaks below, this lands at ~22–23s.

---

## Plain text (paste straight into ElevenLabs)

> When a customer asks AI who to call <break time="0.3s" /> does it say your name?
> <break time="0.5s" />
> Drop in any business URL, and the AI Visibility Audit reads the site the way ChatGPT does <break time="0.3s" /> crawling every page, pulling out the services, scoring how clearly AI understands the business.
> <break time="0.4s" />
> This real Dallas HVAC company scores a D. <break time="0.3s" /> Biggest gap <break time="0.2s" /> AI Recommendation.
> <break time="0.4s" />
> We've audited fifty-plus HVAC sites. The average grade is a C.
> <break time="0.4s" />
> See exactly what AI misses on your site. <break time="0.3s" /> Your grade is free <break time="0.2s" /> sixty seconds.

---

## Pronunciation / TTS notes

- "AI" reads correctly as "A-I". The score name "ABI" is **not spoken** in this
  cut (the badge is on screen).
- "D" (the grade) reads as the standalone capital letter "D." — keep the period.
- "fifty-plus" renders cleaner than "50+"; "sixty seconds" cleaner than "60".
- Keep "ChatGPT" as-is; it renders cleanly.

---

## Muxing back to the video

The Facebook MP4 is currently muted-autoplay (no audio track). For a sound-on
variant, generate the VO above and mux:

```
ffmpeg -i aive_demo_facebook.mp4 -i vo.mp3 \
  -c:v copy -c:a aac -shortest aive_demo_facebook_sound.mp4
```

No offset needed — the VO hook line is written to start on the hook card at t=0.
