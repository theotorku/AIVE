# Demo Voiceover Script — ElevenLabs

Narration for `demo/video/aive-e2e-demo.webm` (the live `dallasheatingac.com`
E2E run). Video length: **23.4s**. Matched to the on-screen segments captured
in `demo/run_e2e.py`.

Brand voice: concrete, operator tone, no emoji, no hype. **Never promise
rankings or recommendations inside AI** — we sell clarity, not placement.

---

## ElevenLabs production settings

- **Model:** Eleven Multilingual v2 (or v3 if you want the bracket emotion tags).
- **Voice:** a calm, credible mid-range male or female (e.g. "Adam", "Daniel",
  "Sarah"). Avoid bright/upsell "ad read" voices — this is a confident demo, not
  a hype reel.
- **Stability:** 50  ·  **Similarity:** 75  ·  **Style:** 0–15  ·  **Speaker boost:** on.
- **Speed:** 1.0. The script targets ~24s of speech; if your render comes in
  short, the trailing pause covers it. If it runs long, nudge Speed to 1.05.
- `<break time="x.xs" />` tags are honored by v2/v3 — they hold the VO to the
  visual beats. Remove them if you'd rather free-run and edit to picture.

---

## Timed script (matched to 23.4s)

| Time | On screen | Line |
|---|---|---|
| 0:00–0:03 | Landing page | Your website works for your customers. The question is whether AI does. |
| 0:03–0:05 | URL entered | Drop in any business URL — |
| 0:05–0:17 | Auditing overlay | — and the AI Visibility Audit reads the site the way ChatGPT or Gemini would: it crawls every page, pulls out the services, and scores how clearly AI can understand the business. |
| 0:17–0:21 | Grade teaser (D, 59.6) | Dallas Heating and Air Conditioning scores a D. The biggest gap — AI Recommendation. |
| 0:21–0:23 | Buy / sample report | One audit shows the gaps, and exactly what to fix. |

Word count: ~62. Spoken at a clear demo pace this lands at ~23–24s.

---

## Plain text (paste straight into ElevenLabs)

> Your website works for your customers. <break time="0.3s" /> The question is whether AI does.
> <break time="0.6s" />
> Drop in any business URL <break time="0.4s" /> and the AI Visibility Audit reads the site the way ChatGPT or Gemini would. <break time="0.3s" /> It crawls every page, pulls out the services, and scores how clearly AI can understand the business.
> <break time="0.5s" />
> Dallas Heating and Air Conditioning scores a D. <break time="0.4s" /> The biggest gap — AI Recommendation.
> <break time="0.4s" />
> One audit shows the gaps, <break time="0.2s" /> and exactly what to fix.

---

## Pronunciation / TTS notes

- "AI" → reads correctly as "A-I". "ABI" the score name is **not spoken** in this
  cut (the badge is on screen); if you want it, write it as "A-B-I" and add
  "fifty-nine point six" rather than "59.6".
- "D" (the grade) reads as the letter — keep it as a standalone capital "D."
- Keep "ChatGPT" and "Gemini" as-is; both render cleanly.

---

## Optional 35–40s extended cut

If you slow the video or add a hold on the grade card, swap the auditing and
closing lines for:

> Drop in any business URL and the AI Visibility Audit reads the site the way an
> AI assistant would. It crawls every page, extracts the services and service
> areas, checks for FAQs, schema, and a way to book — then scores how clearly AI
> can understand, retrieve, and act on the business.
> <break time="0.6s" />
> Dallas Heating and Air Conditioning scores a D — fifty-nine point six. The
> biggest gap is AI Recommendation: no guarantees, certifications, or awards for
> an assistant to stand on.
> <break time="0.6s" />
> The audit shows every gap with the evidence behind it, and the priority fixes.
> That's how you get found, understood, and recommended in AI search.
