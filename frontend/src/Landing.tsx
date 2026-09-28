import { useEffect, useRef, useState, type RefObject } from "react";
import logoUrl from "./assets/aive-logo.png";
import { api, type Teaser } from "./api";

// Live-audit progress copy (mirrors the internal RunPanel stages).
const STAGE_LABEL: Record<string, string> = {
  queued: "Queued…",
  crawling: "Reading your website…",
  extracting: "Understanding your business…",
  scoring: "Scoring AI visibility…",
  done: "Done",
};
const STAGE_PCT: Record<string, number> = {
  queued: 10, crawling: 35, extracting: 70, scoring: 92, done: 100,
};

const PILOT_PRICE = "$399";
const STANDARD_PRICE = "$749";

type Phase = "idle" | "running" | "teaser" | "error";

// Real ABI benchmark — used until the live /api/benchmark readout loads.
const BENCH_FALLBACK = {
  sites: 54,
  avg: 61.5,
  low: 0.8,
  high: 85.7,
  dist: { A: 0, B: 11, C: 26, D: 10, F: 7 } as Record<string, number>,
};

const GRADES = ["A", "B", "C", "D", "F"] as const;

const CHECKS = [
  {
    label: "Business clarity",
    detail: "What you do, who you serve, and where you work.",
  },
  {
    label: "Findability",
    detail: "Pages and facts assistants can retrieve cleanly.",
  },
  {
    label: "Recommendation proof",
    detail: "Trust signals, reviews, credentials, and evidence.",
  },
  {
    label: "Contact readiness",
    detail: "Booking, quote, phone, and form actions agents can find.",
  },
  {
    label: "Content depth",
    detail: "Answers to the questions customers already ask.",
  },
];

const DELIVERABLES = [
  "Overall visibility score",
  "Five check scores",
  "Evidence-backed findings",
  "Priority fixes",
  "Crawl coverage notes",
  "Downloadable report",
  "Review call",
];

const FINDINGS = [
  "Services are listed but not clearly described",
  "Service areas are ambiguous",
  "FAQs are missing or too shallow",
  "Trust signals are weak",
  "Booking or quote actions are hard to find",
  "Structured data is missing",
  "Blog content sends mixed signals",
];

export function Landing({ onSample }: { onSample: () => void }) {
  const [url, setUrl] = useState("");
  const [bench, setBench] = useState(BENCH_FALLBACK);
  const heroInputRef = useRef<HTMLInputElement>(null);
  const finalInputRef = useRef<HTMLInputElement>(null);

  // Live-audit flow (URL → grade teaser → checkout).
  const [phase, setPhase] = useState<Phase>("idle");
  const [stage, setStage] = useState("queued");
  const [teaser, setTeaser] = useState<Teaser | null>(null);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const poll = useRef<number | null>(null);

  useEffect(() => () => { if (poll.current) window.clearInterval(poll.current); }, []);

  useEffect(() => {
    fetch("/api/benchmark")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.benchmark) {
          const b = d.benchmark;
          setBench({
            sites: d.sites_scored,
            avg: b.average_abi,
            low: b.lowest_abi,
            high: b.highest_abi,
            dist: { A: 0, B: 0, C: 0, D: 0, F: 0, ...b.grade_distribution },
          });
        }
      })
      .catch(() => {});
  }, []);

  const runAudit = async () => {
    const clean = url.trim();
    if (!clean) return;
    setPhase("running");
    setStage("queued");
    setAuditError(null);
    setTeaser(null);
    try {
      const job = await api.startRun(clean);
      if (poll.current) window.clearInterval(poll.current);
      poll.current = window.setInterval(async () => {
        try {
          const cur = await api.run(job.run_id);
          setStage(cur.stage);
          if (cur.status === "done" || cur.status === "error") {
            if (poll.current) window.clearInterval(poll.current);
            if (cur.status === "error") {
              setAuditError(cur.error || "The audit failed. Please try another URL.");
              setPhase("error");
              return;
            }
            const t = await api.teaser(cur.domain);
            setTeaser(t);
            setPhase("teaser");
          }
        } catch (e) {
          if (poll.current) window.clearInterval(poll.current);
          setAuditError(e instanceof Error ? e.message : String(e));
          setPhase("error");
        }
      }, 1500);
    } catch (e) {
      setAuditError(e instanceof Error ? e.message : String(e));
      setPhase("error");
    }
  };

  const buyFullAudit = async () => {
    if (!teaser) return;
    setCheckoutLoading(true);
    try {
      const { url: checkoutUrl } = await api.createCheckout(teaser.domain);
      window.location.assign(checkoutUrl);
    } catch (e) {
      setAuditError(e instanceof Error ? e.message : String(e));
      setCheckoutLoading(false);
    }
  };

  const closeOverlay = () => {
    if (poll.current) window.clearInterval(poll.current);
    setPhase("idle");
    setTeaser(null);
    setAuditError(null);
  };

  const submit = (fromRef?: RefObject<HTMLInputElement>) => {
    if (url.trim()) {
      runAudit();
      return;
    }
    (fromRef ?? heroInputRef).current?.focus();
  };

  const distTotal = Object.values(bench.dist).reduce((a, b) => a + b, 0) || 1;
  const distMax = Math.max(...Object.values(bench.dist), 1);
  const lowVisiblePct = Math.round(((bench.dist.D + bench.dist.F) / distTotal) * 100);

  return (
    <main className="sales-page">
      <style>{CSS}</style>

      <header className="sales-nav">
        <a className="sales-mark" href="#top" aria-label="AIVE home">
          <img className="sales-logo" src={logoUrl} alt="AIVE" width={34} height={34} />
          <span>AIVE</span>
        </a>
        <nav className="sales-links" aria-label="Landing page">
          <a href="#checks">Checks</a>
          <a href="#report">Report</a>
          <a href="#findings">Findings</a>
          <a href="#field">Field data</a>
          <button type="button" onClick={onSample}>
            View sample
          </button>
        </nav>
      </header>

      <section className="hero" id="top">
        <div className="hero-visual" aria-hidden="true">
          <div className="signal-map">
            <div className="map-top">
              <span>Website readout</span>
              <b>Visibility</b>
            </div>
            <div className="map-grid">
              <span className="good">Services</span>
              <span>Areas</span>
              <span className="warn">Trust</span>
              <span>FAQs</span>
              <span className="warn">Booking</span>
              <span>Schema</span>
            </div>
            <div className="map-note">
              <span />
              <p>Clear enough to understand. Not yet easy to recommend.</p>
            </div>
          </div>
        </div>

        <div className="hero-copy">
          <p className="eyebrow">AI Visibility Audit</p>
          <h1>Find out if AI recommends your business</h1>
          <p className="hero-text">
            Your site was built for customers and search engines. The audit shows whether
            assistants can understand what you do, trust your business, and find the next
            action a customer should take.
          </p>
          <div className="url-capture" aria-label="Get your AI visibility report">
            <span>https://</span>
            <input
              ref={heroInputRef}
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && submit(heroInputRef)}
              placeholder="yourbusiness.com"
              spellCheck={false}
            />
            <button type="button" onClick={() => submit(heroInputRef)}>
              Get my free grade
            </button>
          </div>
          <button
            className="secondary-link"
            type="button"
            onClick={() => {
              document.getElementById("checks")?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            See what the audit checks
          </button>
        </div>
      </section>

      <section className="problem">
        <div>
          <p className="eyebrow">The shift</p>
          <h2>Your next customer may ask an assistant first.</h2>
        </div>
        <p>
          Those systems need clear facts: what you do, where you serve, why you are
          trustworthy, how customers can contact or book, and whether your site answers
          common questions.
        </p>
        <p>
          If those facts are missing, unclear, or buried, assistants may misunderstand
          your business or recommend a competitor with cleaner signals.
        </p>
      </section>

      <section className="product" id="checks">
        <div className="section-head">
          <p className="eyebrow">What gets checked</p>
          <h2>Five plain checks. One practical report.</h2>
          <p>
            We crawl your website and review the signals that decide whether an assistant
            can understand, retrieve, recommend, and act on your business.
          </p>
        </div>
        <div className="check-list">
          {CHECKS.map((check) => (
            <article className="check-row" key={check.label}>
              <span />
              <div>
                <h3>{check.label}</h3>
                <p>{check.detail}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="report" id="report">
        <div className="report-copy">
          <p className="eyebrow">What you get</p>
          <h2>Evidence, fixes, and a review call.</h2>
          <p>
            The report shows what assistants can read today, where interpretation breaks,
            and which fixes should happen first.
          </p>
        </div>
        <ul className="deliverables">
          {DELIVERABLES.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="why">
        <p className="eyebrow">Why it matters</p>
        <h2>
          The businesses that are easiest to understand are easiest to explain, compare,
          recommend, and contact.
        </h2>
      </section>

      <section className="findings" id="findings">
        <div className="section-head">
          <p className="eyebrow">Sample findings</p>
          <h2>Where recommendations usually break.</h2>
        </div>
        <div className="finding-grid">
          {FINDINGS.map((finding) => (
            <div className="finding" key={finding}>
              <span />
              <p>{finding}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="field" id="field">
        <div className="section-head">
          <p className="eyebrow">Field data</p>
          <h2>We've already scored {bench.sites} real businesses.</h2>
          <p>
            Every audit uses the same scoring your report gets. Here is how the average
            business lands today — and how much room most have to improve.
          </p>
        </div>
        <div className="field-body">
          <div className="field-stats">
            <div className="field-stat">
              <span className="field-n">{bench.avg}</span>
              <span className="field-l">Average score · grade C</span>
            </div>
            <div className="field-stat">
              <span className="field-n">
                {bench.low}
                <i>–</i>
                {bench.high}
              </span>
              <span className="field-l">Range across the benchmark</span>
            </div>
            <div className="field-stat">
              <span className="field-n">{lowVisiblePct}%</span>
              <span className="field-l">Score D or F — hard for AI to recommend</span>
            </div>
          </div>
          <div className="field-dist" role="img" aria-label="Grade distribution across the benchmark">
            {GRADES.map((g) => (
              <div className="dist-col" key={g}>
                <span className="dist-track">
                  <span
                    className="dist-bar"
                    data-grade={g}
                    style={{ height: `${(bench.dist[g] / distMax) * 100 || 1}%` }}
                  />
                </span>
                <span className="dist-g">{g}</span>
                <span className="dist-c">{bench.dist[g]}</span>
              </div>
            ))}
          </div>
        </div>
        <p className="field-note">
          Most common gaps: <b>missing FAQ content</b> · <b>weak heading structure</b> ·{" "}
          <b>no schema.org markup</b>. The fixes are concrete — and usually free.
        </p>
      </section>

      <section className="final-cta">
        <h2>Know how visible your business is to AI.</h2>
        <p>
          Get a clear report showing what assistants can understand from your website
          today and what to improve first.
        </p>
        <div className="url-capture final-capture" aria-label="Get your AI visibility report">
          <span>https://</span>
          <input
            ref={finalInputRef}
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            onKeyDown={(event) => event.key === "Enter" && submit(finalInputRef)}
            placeholder="yourbusiness.com"
            spellCheck={false}
          />
          <button type="button" onClick={() => submit(finalInputRef)}>
            Get my report
          </button>
        </div>
      </section>

      <footer className="sales-footer">
        <p>
          The AI Visibility Audit does not guarantee rankings or recommendations inside
          any specific AI system. It evaluates the clarity, retrievability,
          recommendability, actionability, and authority of your website.
        </p>
      </footer>

      {phase !== "idle" && (
        <div className="audit-overlay" role="dialog" aria-modal="true">
          <div className="audit-card">
            <button className="audit-close" type="button" onClick={closeOverlay} aria-label="Close">
              ×
            </button>

            {phase === "running" && (
              <div className="audit-running">
                <p className="eyebrow">Auditing {url.trim()}</p>
                <h3>{STAGE_LABEL[stage] ?? "Working…"}</h3>
                <div className="audit-track">
                  <span className="audit-fill" style={{ width: `${STAGE_PCT[stage] ?? 10}%` }} />
                </div>
                <p className="audit-sub">
                  We're reading your site the way an AI assistant would. This takes up to a
                  minute.
                </p>
              </div>
            )}

            {phase === "teaser" && teaser && (
              <div className="audit-result">
                <p className="eyebrow">Your AI visibility grade</p>
                <div className="audit-grade" data-grade={teaser.grade ?? "C"}>
                  <span className="audit-letter">{teaser.grade ?? "?"}</span>
                  <span className="audit-score">ABI {teaser.overall ?? "—"}</span>
                </div>
                <h3>{teaser.business_name || teaser.domain}</h3>
                <p className="audit-meaning">{teaser.grade_meaning}</p>

                {teaser.top_gap && (
                  <div className="audit-gap">
                    <span className="audit-gap-label">Biggest gap</span>
                    <b>{teaser.top_gap.title}</b>
                    {teaser.top_gap.why && <p>{teaser.top_gap.why}</p>}
                  </div>
                )}

                <div className="audit-buy">
                  <p className="audit-buy-head">
                    Get the full audit — {PILOT_PRICE}
                  </p>
                  <p className="audit-buy-note">
                    Founding price for the first 10 businesses (normally {STANDARD_PRICE}).
                  </p>
                  <ul className="audit-buy-list">
                    {DELIVERABLES.map((d) => (
                      <li key={d}>{d}</li>
                    ))}
                  </ul>
                  <button
                    className="audit-buy-btn"
                    type="button"
                    onClick={buyFullAudit}
                    disabled={checkoutLoading}
                  >
                    {checkoutLoading ? "Opening checkout…" : `Get the full audit — ${PILOT_PRICE}`}
                  </button>
                  {auditError && <p className="audit-err">{auditError}</p>}
                  <button className="audit-secondary" type="button" onClick={onSample}>
                    See a sample report first
                  </button>
                </div>
              </div>
            )}

            {phase === "error" && (
              <div className="audit-running">
                <p className="eyebrow">Audit failed</p>
                <h3>We couldn't grade that site.</h3>
                <p className="audit-sub">{auditError}</p>
                <button className="audit-buy-btn" type="button" onClick={closeOverlay}>
                  Try another URL
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  );
}

const CSS = `
.sales-page {
  --ink: #11140f;
  --deep: #1b2018;
  --paper: #f7f4ec;
  --muted: #a6ab9c;
  --line: rgba(247, 244, 236, 0.16);
  --line-dark: rgba(17, 20, 15, 0.16);
  --green: #b9ee54;
  --green-dark: #455f1c;
  --clay: #c76f4a;
  --blue: #8ab7c6;
  --gold: #e5bb5f;
  --serif: 'Fraunces', Georgia, serif;
  --sans: 'Hanken Grotesk', system-ui, sans-serif;
  --mono: 'IBM Plex Mono', ui-monospace, monospace;
  min-height: 100vh;
  background: var(--ink);
  color: var(--paper);
  font-family: var(--sans);
  overflow-x: hidden;
}

.sales-page * {
  box-sizing: border-box;
}

.sales-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px clamp(18px, 4vw, 52px);
  background: linear-gradient(180deg, rgba(17, 20, 15, 0.86), rgba(17, 20, 15, 0));
}

.sales-mark,
.sales-links,
.url-capture,
.check-row,
.finding {
  display: flex;
  align-items: center;
}

.sales-mark {
  gap: 10px;
  color: var(--paper);
  text-decoration: none;
  font-family: var(--serif);
  font-size: 1.22rem;
  font-weight: 600;
}

.sales-logo {
  display: block;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  object-fit: contain;
}

.sales-links {
  gap: 24px;
  font-size: 0.86rem;
}

.sales-links a,
.sales-links button,
.secondary-link {
  border: 0;
  background: none;
  color: var(--muted);
  cursor: pointer;
  font: inherit;
  text-decoration: none;
}

.sales-links button {
  color: var(--paper);
  border-bottom: 1px solid var(--green);
  padding: 0 0 3px;
}

.sales-links a:hover,
.sales-links button:hover,
.secondary-link:hover {
  color: var(--green);
}

.hero {
  position: relative;
  display: grid;
  min-height: min(760px, 100svh);
  grid-template-columns: minmax(300px, 0.88fr) minmax(420px, 1fr);
  gap: clamp(28px, 6vw, 86px);
  align-items: center;
  padding: 94px clamp(18px, 5vw, 70px) clamp(34px, 5vw, 58px);
  isolation: isolate;
}

.hero::after {
  position: absolute;
  inset: 0;
  z-index: -2;
  content: "";
  background:
    linear-gradient(90deg, rgba(17, 20, 15, 0.72), rgba(17, 20, 15, 0.94)),
    radial-gradient(circle at 18% 28%, rgba(138, 183, 198, 0.24), transparent 29%),
    radial-gradient(circle at 68% 78%, rgba(199, 111, 74, 0.18), transparent 30%),
    linear-gradient(135deg, #1b2018, #0d100c);
}

.hero-visual {
  position: relative;
  min-height: 480px;
}

.hero-visual::before,
.hero-visual::after {
  position: absolute;
  content: "";
  border: 1px solid rgba(247, 244, 236, 0.18);
}

.hero-visual::before {
  width: 78%;
  height: 38%;
  left: -7%;
  top: 5%;
  border-color: rgba(185, 238, 84, 0.22);
  transform: rotate(-15deg);
  animation: drift 12s ease-in-out infinite alternate;
}

.hero-visual::after {
  width: 62%;
  height: 52%;
  right: 2%;
  bottom: 2%;
  border-color: rgba(138, 183, 198, 0.24);
  transform: rotate(9deg);
  animation: driftSoft 14s ease-in-out infinite alternate;
}

.signal-map {
  position: absolute;
  left: 4%;
  right: 7%;
  top: 14%;
  z-index: 1;
  padding: 26px;
  border: 1px solid rgba(247, 244, 236, 0.18);
  background:
    linear-gradient(180deg, rgba(247, 244, 236, 0.13), rgba(247, 244, 236, 0.04)),
    rgba(17, 20, 15, 0.66);
  box-shadow: 0 34px 120px rgba(0, 0, 0, 0.42);
  backdrop-filter: blur(14px);
  transform: rotate(-2deg);
}

.map-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 42px;
}

.map-top span {
  color: var(--muted);
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.map-top b {
  color: var(--green);
  font-size: 1rem;
  font-weight: 700;
}

.map-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.map-grid span {
  min-height: 86px;
  display: flex;
  align-items: flex-end;
  padding: 12px;
  border: 1px solid rgba(247, 244, 236, 0.16);
  background: rgba(247, 244, 236, 0.06);
  color: #d7d3c8;
  font-size: 0.86rem;
}

.map-grid .good {
  border-color: rgba(185, 238, 84, 0.5);
  background: rgba(185, 238, 84, 0.12);
}

.map-grid .warn {
  border-color: rgba(229, 187, 95, 0.46);
  background: rgba(229, 187, 95, 0.1);
}

.map-note {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid rgba(247, 244, 236, 0.16);
}

.map-note span {
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
  margin-top: 6px;
  border-radius: 50%;
  background: var(--gold);
}

.map-note p {
  margin: 0;
  color: #d7d3c8;
  font-size: 0.98rem;
  line-height: 1.45;
}

.hero-copy {
  max-width: 680px;
  animation: rise 700ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

.eyebrow {
  margin: 0 0 14px;
  color: var(--green);
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

h1,
h2,
h3,
p {
  margin-top: 0;
}

h1,
h2,
h3 {
  font-family: var(--sans);
  font-weight: 800;
  letter-spacing: 0;
}

h1 {
  max-width: 10em;
  margin-bottom: 20px;
  font-size: clamp(2.9rem, 6.2vw, 5.8rem);
  line-height: 0.96;
}

.hero-text {
  max-width: 40rem;
  color: #d7d3c8;
  font-size: clamp(1.05rem, 1.5vw, 1.2rem);
  line-height: 1.55;
}

.url-capture {
  width: min(100%, 640px);
  margin-top: 28px;
  gap: 8px;
  padding: 7px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(17, 20, 15, 0.72);
}

.url-capture:focus-within {
  border-color: var(--green);
  box-shadow: 0 0 0 4px rgba(185, 238, 84, 0.12);
}

.url-capture span {
  padding-left: 10px;
  color: var(--muted);
  font-family: var(--sans);
  font-size: 0.92rem;
}

.url-capture input {
  min-width: 0;
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--paper);
  font-family: var(--sans);
  font-size: 1rem;
}

.url-capture button {
  border: 0;
  border-radius: 5px;
  background: var(--green);
  color: #14210c;
  cursor: pointer;
  font-family: var(--sans);
  font-size: 0.92rem;
  font-weight: 800;
  padding: 14px 17px;
  white-space: nowrap;
}

.url-capture button:hover {
  background: #cbff68;
}

.secondary-link {
  margin-top: 16px;
  padding: 0;
  font-size: 0.92rem;
  text-decoration: underline;
  text-underline-offset: 5px;
}

.problem,
.product,
.report,
.why,
.findings,
.field,
.final-cta,
.sales-footer {
  padding: clamp(56px, 7vw, 92px) clamp(18px, 5vw, 70px);
}

.problem {
  display: grid;
  grid-template-columns: minmax(260px, 0.78fr) 1fr 1fr;
  gap: clamp(24px, 4vw, 58px);
  border-top: 1px solid var(--line);
}

.problem h2,
.section-head h2,
.report-copy h2,
.final-cta h2 {
  font-size: clamp(2rem, 3.4vw, 3.35rem);
  line-height: 1.02;
}

.problem p,
.section-head p,
.report-copy p,
.final-cta p,
.sales-footer p {
  color: #d0ccbf;
  font-size: 1.03rem;
  line-height: 1.64;
}

.product,
.findings {
  background: var(--paper);
  color: var(--ink);
}

.product .eyebrow,
.findings .eyebrow {
  color: var(--green-dark);
}

.section-head {
  max-width: 720px;
  margin-bottom: 34px;
}

.section-head p,
.product .check-row p,
.findings .finding p {
  color: #565a4f;
}

.check-list {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 1px;
  background: var(--line-dark);
}

.check-row {
  min-height: 210px;
  flex-direction: column;
  align-items: flex-start;
  justify-content: space-between;
  gap: 34px;
  padding: 22px;
  background: var(--paper);
}

.check-row span {
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: var(--green-dark);
}

.check-row h3 {
  margin: 0 0 8px;
  font-size: 1.35rem;
  line-height: 1.05;
}

.check-row p {
  margin: 0;
}

.report {
  display: grid;
  grid-template-columns: minmax(280px, 0.78fr) 1fr;
  gap: clamp(30px, 6vw, 78px);
  align-items: start;
  background: #20251b;
}

.deliverables {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.deliverables li {
  flex: 1 1 180px;
  min-height: 70px;
  display: flex;
  align-items: center;
  padding: 18px;
  border: 1px solid var(--line);
  color: var(--paper);
  font-size: 0.96rem;
  font-weight: 700;
}

.why {
  background: var(--blue);
  color: #101816;
}

.why .eyebrow {
  color: #173631;
}

.why h2 {
  max-width: 980px;
  margin-bottom: 0;
  font-size: clamp(2rem, 4vw, 4.2rem);
  line-height: 1.03;
}

.finding-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(150px, 1fr));
  gap: 1px;
  overflow-x: auto;
  background: var(--line-dark);
}

.finding {
  min-height: 210px;
  align-items: flex-start;
  flex-direction: column;
  justify-content: space-between;
  gap: 32px;
  padding: 20px;
  background: var(--paper);
}

.finding span {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--clay);
}

.finding:nth-child(2n) span {
  background: var(--gold);
}

.finding:nth-child(3n) span {
  background: var(--blue);
}

.finding p {
  margin: 0;
  font-size: 1.16rem;
  font-weight: 800;
  line-height: 1.14;
}

.field {
  background: #20251b;
}

.field-body {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: clamp(30px, 5vw, 70px);
  align-items: end;
}

.field-stats {
  display: grid;
  grid-template-columns: 1fr;
  gap: 26px;
}

.field-stat {
  padding-top: 16px;
  border-top: 2px solid var(--green);
}

.field-n {
  display: block;
  font-family: var(--serif);
  font-weight: 600;
  font-size: clamp(2.4rem, 5vw, 3.6rem);
  line-height: 1;
  letter-spacing: -0.02em;
  color: var(--paper);
}

.field-n i {
  font-style: normal;
  color: var(--muted);
  margin: 0 4px;
}

.field-l {
  display: block;
  margin-top: 10px;
  font-family: var(--mono);
  font-size: 0.74rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
}

.field-dist {
  display: flex;
  align-items: flex-end;
  gap: clamp(10px, 2vw, 22px);
  height: 220px;
  padding-bottom: 4px;
  border-bottom: 2px solid var(--line);
}

.dist-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
  gap: 10px;
}

.dist-track {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
}

.dist-bar {
  width: 100%;
  min-height: 3px;
  border-radius: 6px 6px 0 0;
  transition: height 0.8s cubic-bezier(0.2, 0.7, 0.2, 1);
}

.dist-bar[data-grade="A"] { background: #7bd88f; }
.dist-bar[data-grade="B"] { background: var(--green); }
.dist-bar[data-grade="C"] { background: var(--gold); }
.dist-bar[data-grade="D"] { background: var(--clay); }
.dist-bar[data-grade="F"] { background: #d1503f; }

.dist-g {
  font-family: var(--serif);
  font-weight: 600;
  font-size: 1.1rem;
  color: var(--paper);
}

.dist-c {
  font-family: var(--mono);
  font-size: 0.72rem;
  color: var(--muted);
}

.field-note {
  max-width: 60em;
  margin: 34px 0 0;
  color: #d0ccbf;
  font-size: 1rem;
  line-height: 1.6;
}

.field-note b {
  color: var(--paper);
}

.final-cta {
  display: grid;
  place-items: center;
  text-align: center;
  background:
    radial-gradient(circle at 50% 0%, rgba(185, 238, 84, 0.14), transparent 34%),
    var(--ink);
}

.final-cta h2 {
  max-width: 720px;
  margin-bottom: 16px;
}

.final-cta p {
  max-width: 620px;
  margin-bottom: 0;
}

.final-capture {
  margin-inline: auto;
}

.sales-footer {
  padding-top: 32px;
  padding-bottom: 42px;
  border-top: 1px solid var(--line);
  background: var(--ink);
}

.sales-footer p {
  max-width: 920px;
  margin: 0 auto;
  color: var(--muted);
  font-size: 0.9rem;
  text-align: center;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@keyframes drift {
  from {
    transform: translate3d(0, 0, 0) rotate(-15deg);
  }
  to {
    transform: translate3d(2vw, -2vh, 0) rotate(-10deg);
  }
}

@keyframes driftSoft {
  from {
    transform: translate3d(0, 0, 0) rotate(9deg);
  }
  to {
    transform: translate3d(-1vw, 2vh, 0) rotate(5deg);
  }
}

@media (max-width: 1040px) {
  .hero {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .hero-visual {
    min-height: 360px;
    order: 2;
  }

  .hero-copy {
    order: 1;
    padding-top: 48px;
  }

  .signal-map {
    left: 0;
    right: 0;
    top: 8%;
  }

  .problem,
  .report,
  .field-body {
    grid-template-columns: 1fr;
  }

  .field-dist {
    height: 180px;
  }

  .check-list,
  .finding-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .sales-nav {
    padding: 14px 16px;
  }

  .sales-links {
    gap: 12px;
  }

  .sales-links a {
    display: none;
  }

  .sales-links button {
    font-size: 0.82rem;
  }

  .hero {
    padding-top: 82px;
  }

  h1 {
    font-size: clamp(2.55rem, 14vw, 4rem);
  }

  .hero-visual {
    min-height: 315px;
  }

  .signal-map {
    padding: 18px;
  }

  .map-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .map-grid span {
    min-height: 62px;
  }

  .url-capture {
    align-items: stretch;
    flex-wrap: wrap;
  }

  .url-capture input {
    min-height: 42px;
  }

  .url-capture button {
    width: 100%;
  }

  .check-list,
  .finding-grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero-copy,
  .hero-visual::before,
  .hero-visual::after {
    animation: none;
  }

  .dist-bar {
    transition: none;
  }
}

/* --- Live audit overlay (URL → grade teaser → checkout) --- */
.audit-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(8, 10, 7, 0.72);
  backdrop-filter: blur(6px);
  animation: rise 240ms ease both;
}

.audit-card {
  position: relative;
  width: min(560px, 100%);
  max-height: 92vh;
  overflow-y: auto;
  padding: clamp(26px, 4vw, 40px);
  border: 1px solid var(--line);
  border-radius: 14px;
  background: linear-gradient(180deg, #20251b, #14180f);
  box-shadow: 0 40px 120px rgba(0, 0, 0, 0.5);
}

.audit-close {
  position: absolute;
  top: 14px;
  right: 16px;
  border: 0;
  background: none;
  color: var(--muted);
  font-size: 1.6rem;
  line-height: 1;
  cursor: pointer;
}

.audit-close:hover { color: var(--paper); }

.audit-running h3,
.audit-result h3 {
  margin: 6px 0 0;
  font-size: 1.5rem;
}

.audit-sub {
  margin: 14px 0 0;
  color: #cfcbbe;
  font-size: 0.98rem;
  line-height: 1.5;
}

.audit-track {
  margin-top: 18px;
  height: 8px;
  border-radius: 999px;
  background: rgba(247, 244, 236, 0.12);
  overflow: hidden;
}

.audit-fill {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: var(--green);
  transition: width 0.7s cubic-bezier(0.2, 0.7, 0.2, 1);
}

.audit-grade {
  display: flex;
  align-items: baseline;
  gap: 14px;
  margin: 10px 0 4px;
}

.audit-letter {
  font-family: var(--serif);
  font-weight: 600;
  font-size: 3.6rem;
  line-height: 1;
}

.audit-grade[data-grade="A"] .audit-letter { color: #7bd88f; }
.audit-grade[data-grade="B"] .audit-letter { color: var(--green); }
.audit-grade[data-grade="C"] .audit-letter { color: var(--gold); }
.audit-grade[data-grade="D"] .audit-letter { color: var(--clay); }
.audit-grade[data-grade="F"] .audit-letter { color: #d1503f; }

.audit-score {
  font-family: var(--mono);
  font-size: 0.95rem;
  color: var(--muted);
}

.audit-meaning {
  margin: 8px 0 0;
  color: #d7d3c8;
  font-size: 1.02rem;
  line-height: 1.5;
}

.audit-gap {
  margin-top: 20px;
  padding: 16px 18px;
  border: 1px solid rgba(199, 111, 74, 0.4);
  border-radius: 10px;
  background: rgba(199, 111, 74, 0.1);
}

.audit-gap-label {
  display: block;
  font-family: var(--mono);
  font-size: 0.68rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--clay);
}

.audit-gap b {
  display: block;
  margin-top: 6px;
  font-size: 1.08rem;
}

.audit-gap p {
  margin: 8px 0 0;
  color: #d0ccbf;
  font-size: 0.94rem;
  line-height: 1.5;
}

.audit-buy {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--line);
}

.audit-buy-head {
  margin: 0 0 6px;
  font-family: var(--serif);
  font-size: 1.2rem;
  color: var(--paper);
}

.audit-buy-note {
  margin: 0 0 12px;
  font-size: 0.82rem;
  color: var(--muted, #9a958c);
}

.audit-buy-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 16px;
  margin: 0 0 18px;
  padding: 0;
  list-style: none;
  color: #cfcbbe;
  font-size: 0.88rem;
}

.audit-buy-list li {
  position: relative;
  padding-left: 18px;
}

.audit-buy-list li::before {
  content: "✓";
  position: absolute;
  left: 0;
  color: var(--green);
}

.audit-buy-btn {
  width: 100%;
  padding: 15px 18px;
  border: 0;
  border-radius: 7px;
  background: var(--green);
  color: #14210c;
  font-family: var(--sans);
  font-size: 1rem;
  font-weight: 800;
  cursor: pointer;
}

.audit-buy-btn:hover { background: #cbff68; }
.audit-buy-btn:disabled { opacity: 0.6; cursor: default; }

.audit-secondary {
  display: block;
  width: 100%;
  margin-top: 12px;
  border: 0;
  background: none;
  color: var(--muted);
  font: inherit;
  font-size: 0.9rem;
  text-decoration: underline;
  text-underline-offset: 4px;
  cursor: pointer;
}

.audit-secondary:hover { color: var(--green); }

.audit-err {
  margin: 12px 0 0;
  color: #f0a58d;
  font-size: 0.9rem;
}

@media (max-width: 560px) {
  .audit-buy-list { grid-template-columns: 1fr; }
}
`;
