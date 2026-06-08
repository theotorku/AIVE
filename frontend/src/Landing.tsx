import { useEffect, useState } from "react";

/**
 * AIVE marketing landing page — "AI Visibility Audit".
 * Self-contained: its own scoped CSS + fonts (loaded in index.html). The CTAs
 * lead into the real dashboard (App). Numbers shown are the real ABI benchmark.
 */

const BENCH_FALLBACK = {
  sites: 54, avg: 61.5, low: 0.8, high: 85.7,
  dist: { A: 0, B: 11, C: 26, D: 10, F: 7 } as Record<string, number>,
};

// Real per-dimension benchmark averages (the "average business" readout).
const DIMS = [
  { n: "01", k: "Understanding", q: "Can AI tell what your business does?", w: 25, v: 81 },
  { n: "02", k: "Findability", q: "Can AI find and pull up your content?", w: 25, v: 53 },
  { n: "03", k: "Trust", q: "Will AI feel confident recommending you?", w: 20, v: 62 },
  { n: "04", k: "Action-ready", q: "Can an AI agent book or contact you?", w: 15, v: 48 },
  { n: "05", k: "Authority", q: "Does AI see you as a credible source?", w: 15, v: 56 },
];

const ENGINES = ["ChatGPT", "Claude", "Gemini", "Perplexity", "Copilot"];

export function Landing({
  onAudit,
  onSample,
}: {
  onAudit: (url: string) => void;
  onSample: () => void;
}) {
  const [url, setUrl] = useState("");
  const [bench, setBench] = useState(BENCH_FALLBACK);

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

  const submit = () => {
    if (url.trim()) onAudit(url.trim());
  };

  const distTotal = Object.values(bench.dist).reduce((a, b) => a + b, 0) || 1;

  return (
    <div className="av">
      <style>{CSS}</style>
      <div className="av-grain" aria-hidden />

      {/* NAV */}
      <header className="av-nav">
        <div className="av-wrap av-nav-in">
          <div className="av-brand">
            <span className="av-logo">◢◣</span>
            <span className="av-word">AIVE</span>
            <span className="av-tag">AI&nbsp;VISIBILITY&nbsp;AUDIT</span>
          </div>
          <nav className="av-nav-links">
            <a href="#measure">What we measure</a>
            <a href="#how">How it works</a>
            <a href="#proof">Field data</a>
            <button className="av-btn av-btn-ghost" onClick={onSample}>
              See a real audit
            </button>
          </nav>
        </div>
      </header>

      {/* HERO */}
      <section className="av-hero">
        <div className="av-wrap av-hero-grid">
          <div className="av-hero-copy">
            <div className="av-eyebrow av-rise" style={{ animationDelay: "40ms" }}>
              <span className="av-dot" /> AI VISIBILITY AUDIT · POWERED BY ABI
            </div>
            <h1 className="av-h1 av-rise" style={{ animationDelay: "120ms" }}>
              What does AI <em>see</em> when it reads your business?
            </h1>
            <p className="av-lede av-rise" style={{ animationDelay: "220ms" }}>
              Search engines optimized you for humans. <strong>AIVE</strong> measures — and
              fixes — how well ChatGPT, Claude, Gemini, and Perplexity can understand,
              trust, and recommend you. One grade. Five signals. The exact fixes.
            </p>

            <div className="av-cta av-rise" style={{ animationDelay: "320ms" }}>
              <div className="av-field">
                <span className="av-field-pre">https://</span>
                <input
                  className="av-input"
                  placeholder="yourbusiness.com"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && submit()}
                  spellCheck={false}
                />
                <button className="av-btn av-btn-go" onClick={submit}>
                  Run free audit →
                </button>
              </div>
              <p className="av-fine">
                No signup · runs in ~30s · real grade, real evidence ·{" "}
                <button className="av-link" onClick={onSample}>
                  or see a real audit →
                </button>
              </p>
            </div>
          </div>

          {/* INSTRUMENT READOUT */}
          <div className="av-readout av-rise" style={{ animationDelay: "260ms" }}>
            <div className="av-scan" aria-hidden />
            <div className="av-readout-head">
              <span>ABI://READOUT</span>
              <span className="av-blink">● LIVE</span>
            </div>
            <div className="av-readout-grade">
              <div className="av-grade av-grade-C">C</div>
              <div className="av-grade-meta">
                <div className="av-grade-score">ABI 61</div>
                <div className="av-grade-label">Partially visible</div>
                <div className="av-grade-sub">Industry average · {bench.sites} businesses</div>
              </div>
            </div>
            <div className="av-bars">
              {DIMS.map((d, i) => (
                <div className="av-bar-row" key={d.k}>
                  <span className="av-bar-label">{d.k}</span>
                  <span className="av-bar-track">
                    <span
                      className="av-bar-fill"
                      style={{ width: `${d.v}%`, animationDelay: `${600 + i * 120}ms` }}
                    />
                  </span>
                  <span className="av-bar-val">{d.v}</span>
                </div>
              ))}
            </div>
            <div className="av-readout-foot">
              SCAN COMPLETE · 5 SIGNALS · {bench.sites} SITES BENCHMARKED
            </div>
          </div>
        </div>

        <div className="av-marquee" aria-hidden>
          <div className="av-marquee-in">
            {[...ENGINES, ...ENGINES, ...ENGINES].map((e, i) => (
              <span key={i}>
                {e} <i>/</i>
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* THE SHIFT */}
      <section className="av-shift">
        <div className="av-wrap">
          <div className="av-kicker">THE OPTIMIZATION TARGET MOVED</div>
          <div className="av-shift-grid">
            <div className="av-shift-col av-was">
              <span className="av-shift-when">YESTERDAY</span>
              <ul>
                <li>Websites</li>
                <li>SEO &amp; keywords</li>
                <li>Ten blue links</li>
                <li>Built for human eyes</li>
              </ul>
            </div>
            <div className="av-shift-arrow">→</div>
            <div className="av-shift-col av-now">
              <span className="av-shift-when av-now-when">TODAY</span>
              <ul>
                <li>Answer engines</li>
                <li>AI assistants</li>
                <li>Autonomous agents</li>
                <li>Built for machine reading</li>
              </ul>
            </div>
          </div>
          <p className="av-shift-line">
            Your next customer increasingly meets you through an AI first — and{" "}
            <em>most businesses are invisible to it.</em> Poor structure, weak FAQs,
            ambiguous services, no machine-readable markup. The AI can't understand you,
            so it can't recommend you.
          </p>
        </div>
      </section>

      {/* WHAT WE MEASURE */}
      <section className="av-measure" id="measure">
        <div className="av-wrap">
          <div className="av-sec-head">
            <div className="av-kicker">THE AGENT BUSINESS INDEX</div>
            <h2 className="av-h2">Five signals. One grade from A to F.</h2>
            <p className="av-sec-sub">
              Every audit reads your site the way an AI agent does, then scores the five
              things that decide whether you get understood, retrieved, and recommended.
            </p>
          </div>
          <div className="av-dims">
            {DIMS.map((d) => (
              <div className="av-dim" key={d.k}>
                <div className="av-dim-top">
                  <span className="av-dim-n">{d.n}</span>
                  <span className="av-dim-w">{d.w}%</span>
                </div>
                <h3 className="av-dim-k">{d.k}</h3>
                <p className="av-dim-q">{d.q}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="av-how" id="how">
        <div className="av-wrap av-how-grid">
          <div className="av-how-head">
            <div className="av-kicker av-kicker-dark">HOW IT WORKS</div>
            <h2 className="av-h2 av-h2-dark">A grade in three steps.</h2>
          </div>
          <ol className="av-steps">
            <li>
              <span className="av-step-n">01</span>
              <div>
                <h4>Drop in your URL</h4>
                <p>No tags, no setup, no signup. Just your website address.</p>
              </div>
            </li>
            <li>
              <span className="av-step-n">02</span>
              <div>
                <h4>We read it like an AI</h4>
                <p>
                  We crawl, extract your business intelligence, and judge it on the exact
                  signals answer engines use — with the evidence behind every point.
                </p>
              </div>
            </li>
            <li>
              <span className="av-step-n">03</span>
              <div>
                <h4>Get your grade &amp; top 3 fixes</h4>
                <p>
                  Your ABI grade, why you got it, and the highest-leverage fixes — in plain
                  language a non-technical owner gets in 60 seconds.
                </p>
              </div>
            </li>
          </ol>
        </div>
      </section>

      {/* PROOF / FIELD DATA */}
      <section className="av-proof" id="proof">
        <div className="av-wrap">
          <div className="av-kicker">FIELD DATA</div>
          <h2 className="av-h2">We've already audited {bench.sites} real businesses.</h2>
          <div className="av-stats">
            <div className="av-stat">
              <span className="av-stat-n">{bench.avg}</span>
              <span className="av-stat-l">Average ABI · grade C</span>
            </div>
            <div className="av-stat">
              <span className="av-stat-n">
                {bench.low}<i>–</i>{bench.high}
              </span>
              <span className="av-stat-l">Full range across the benchmark</span>
            </div>
            <div className="av-stat">
              <span className="av-stat-n">
                {Math.round(((bench.dist.D + bench.dist.F) / distTotal) * 100)}%
              </span>
              <span className="av-stat-l">Score D or F — barely visible to AI</span>
            </div>
          </div>
          <div className="av-dist">
            {(["A", "B", "C", "D", "F"] as const).map((g) => (
              <div className="av-dist-col" key={g}>
                <span className="av-dist-bar-wrap">
                  <span
                    className={`av-dist-bar av-fill-${g}`}
                    style={{ height: `${(bench.dist[g] / distTotal) * 100 || 1}%` }}
                  />
                </span>
                <span className="av-dist-g">{g}</span>
                <span className="av-dist-c">{bench.dist[g]}</span>
              </div>
            ))}
          </div>
          <p className="av-proof-gaps">
            Most common gaps: <b>missing FAQ content</b> · <b>weak heading structure</b> ·{" "}
            <b>no schema.org markup</b>. The fixes are concrete — and usually free.
          </p>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="av-final">
        <div className="av-wrap av-final-in">
          <h2 className="av-final-h">
            Find out what AI <em>sees</em>.
          </h2>
          <p className="av-final-sub">Your free AI Visibility Audit takes about 30 seconds.</p>
          <div className="av-field av-field-lg">
            <span className="av-field-pre">https://</span>
            <input
              className="av-input"
              placeholder="yourbusiness.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
              spellCheck={false}
            />
            <button className="av-btn av-btn-go" onClick={submit}>
              Run free audit →
            </button>
          </div>
          <button className="av-link av-link-lg" onClick={onSample}>
            or explore a real audit first →
          </button>
        </div>
      </section>

      <footer className="av-foot">
        <div className="av-wrap av-foot-in">
          <div className="av-brand">
            <span className="av-logo">◢◣</span>
            <span className="av-word">AIVE</span>
          </div>
          <span className="av-foot-mid">
            AI Visibility Audit · scored by the Agent Business Index (ABI v0.1.1)
          </span>
          <span className="av-foot-r">Make your business understandable to AI.</span>
        </div>
      </footer>
    </div>
  );
}

const CSS = `
.av{
  --ink:#0c0e0b; --ink2:#12150e; --ink3:#181c12;
  --paper:#f3f0e7; --paper2:#e9e5d8;
  --fog:#9b9d8e; --fog2:#73766a;
  --line:rgba(243,240,231,.12); --line-dk:rgba(12,14,11,.12);
  --signal:#c6f04a; --signal-deep:#aee03a;
  --A:#7bd88f; --B:#b6e34a; --C:#f2c14e; --D:#f0883c; --F:#ff5a47;
  --serif:'Fraunces',Georgia,serif;
  --mono:'IBM Plex Mono',ui-monospace,monospace;
  --sans:'Hanken Grotesk',system-ui,sans-serif;
  background:var(--ink); color:var(--paper);
  font-family:var(--sans); line-height:1.5; -webkit-font-smoothing:antialiased;
  overflow-x:hidden; position:relative;
}
.av *{box-sizing:border-box; margin:0; padding:0;}
.av-wrap{max-width:1180px; margin:0 auto; padding:0 28px;}
.av-grain{position:fixed; inset:0; z-index:0; pointer-events:none; opacity:.05;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");}
.av section,.av header,.av footer{position:relative; z-index:1;}

/* type */
.av-h1{font-family:var(--serif); font-weight:600; font-size:clamp(2.6rem,6.2vw,5.1rem);
  line-height:.98; letter-spacing:-.02em; color:var(--paper);}
.av-h1 em{font-style:italic; color:var(--signal); font-weight:500;}
.av-h2{font-family:var(--serif); font-weight:600; font-size:clamp(1.9rem,3.6vw,3rem);
  line-height:1.02; letter-spacing:-.015em; color:var(--paper);}
.av-h2-dark{color:var(--ink);}
.av-kicker{font-family:var(--mono); font-size:.72rem; letter-spacing:.32em;
  color:var(--signal-deep); text-transform:uppercase; margin-bottom:18px;}
.av-kicker-dark{color:#3f5a16;}

/* nav */
.av-nav{position:sticky; top:0; z-index:40; backdrop-filter:blur(10px);
  background:rgba(12,14,11,.72); border-bottom:1px solid var(--line);}
.av-nav-in{display:flex; align-items:center; justify-content:space-between; height:64px;}
.av-brand{display:flex; align-items:center; gap:10px;}
.av-logo{color:var(--signal); font-size:1rem; letter-spacing:-2px;}
.av-word{font-family:var(--serif); font-weight:600; font-size:1.35rem; letter-spacing:.02em;}
.av-tag{font-family:var(--mono); font-size:.6rem; letter-spacing:.22em; color:var(--fog);
  border:1px solid var(--line); padding:3px 7px; border-radius:4px;}
.av-nav-links{display:flex; align-items:center; gap:26px;}
.av-nav-links a{color:var(--fog); text-decoration:none; font-size:.86rem; transition:color .15s;}
.av-nav-links a:hover{color:var(--paper);}
@media(max-width:760px){.av-nav-links a{display:none;}}

/* buttons */
.av-btn{font-family:var(--mono); font-size:.8rem; letter-spacing:.04em; cursor:pointer;
  border:none; border-radius:7px; padding:11px 16px; transition:transform .12s,background .15s,box-shadow .15s;}
.av-btn:active{transform:translateY(1px);}
.av-btn-ghost{background:transparent; color:var(--paper); border:1px solid var(--line);}
.av-btn-ghost:hover{border-color:var(--signal); color:var(--signal);}
.av-btn-go{background:var(--signal); color:#10210a; font-weight:600; white-space:nowrap;
  box-shadow:0 0 0 0 rgba(198,240,74,.5);}
.av-btn-go:hover{background:var(--signal-deep); box-shadow:0 0 26px -4px rgba(198,240,74,.55);}
.av-link{background:none; border:none; color:var(--signal-deep); cursor:pointer;
  font:inherit; text-decoration:underline; text-underline-offset:3px;}
.av-link:hover{color:var(--signal);}

/* hero */
.av-hero{padding-top:54px;}
.av-hero-grid{display:grid; grid-template-columns:1.1fr .9fr; gap:54px; align-items:center;
  padding-bottom:38px;}
@media(max-width:920px){.av-hero-grid{grid-template-columns:1fr; gap:38px;}}
.av-eyebrow{display:inline-flex; align-items:center; gap:9px; font-family:var(--mono);
  font-size:.72rem; letter-spacing:.2em; color:var(--fog);}
.av-dot{width:7px; height:7px; border-radius:50%; background:var(--signal);
  box-shadow:0 0 10px var(--signal); animation:avpulse 2s infinite;}
.av-h1{margin:18px 0 0;}
.av-lede{margin-top:22px; font-size:clamp(1.02rem,1.5vw,1.22rem); color:#cfccc0; max-width:33em;}
.av-lede strong{color:var(--paper); font-weight:700;}
.av-cta{margin-top:30px;}
.av-field{display:flex; align-items:stretch; background:var(--ink2);
  border:1px solid var(--line); border-radius:11px; padding:6px; gap:4px; max-width:520px;
  transition:border-color .15s, box-shadow .15s;}
.av-field:focus-within{border-color:var(--signal); box-shadow:0 0 0 4px rgba(198,240,74,.1);}
.av-field-pre{display:flex; align-items:center; padding:0 4px 0 12px; color:var(--fog2);
  font-family:var(--mono); font-size:.86rem;}
.av-input{flex:1; min-width:0; background:transparent; border:none; outline:none;
  color:var(--paper); font-family:var(--mono); font-size:.95rem; padding:11px 6px;}
.av-input::placeholder{color:var(--fog2);}
.av-fine{margin-top:14px; font-size:.82rem; color:var(--fog);}
.av-fine .av-link{font-size:.82rem;}

/* readout */
.av-readout{position:relative; background:linear-gradient(180deg,#14180f,#0e110a);
  border:1px solid var(--line); border-radius:16px; padding:22px; overflow:hidden;
  box-shadow:0 40px 80px -40px rgba(0,0,0,.8), inset 0 1px 0 rgba(243,240,231,.04);}
.av-readout::before{content:""; position:absolute; inset:0;
  background:radial-gradient(120% 80% at 80% 0,rgba(198,240,74,.08),transparent 60%);}
.av-scan{position:absolute; left:0; right:0; top:0; height:90px; z-index:3; pointer-events:none;
  background:linear-gradient(180deg,rgba(198,240,74,.22),transparent);
  animation:avscan 2.6s cubic-bezier(.4,0,.2,1) 1 forwards;}
.av-readout-head{display:flex; justify-content:space-between; font-family:var(--mono);
  font-size:.68rem; letter-spacing:.18em; color:var(--fog); position:relative;}
.av-blink{color:var(--signal);}
.av-readout-grade{display:flex; align-items:center; gap:18px; margin:18px 0 22px; position:relative;}
.av-grade{font-family:var(--serif); font-weight:600; font-size:5.4rem; line-height:.82;
  width:108px; height:108px; display:flex; align-items:center; justify-content:center;
  border-radius:14px; color:#10210a; animation:avpop .5s .5s both;}
.av-grade-C{background:var(--C);}
.av-grade-meta{}
.av-grade-score{font-family:var(--mono); font-size:1.5rem; color:var(--paper); font-weight:600;}
.av-grade-label{font-family:var(--serif); font-style:italic; font-size:1.25rem; color:var(--C);}
.av-grade-sub{font-family:var(--mono); font-size:.68rem; letter-spacing:.1em; color:var(--fog); margin-top:6px;}
.av-bars{display:flex; flex-direction:column; gap:11px; position:relative;}
.av-bar-row{display:grid; grid-template-columns:104px 1fr 30px; align-items:center; gap:12px;}
.av-bar-label{font-family:var(--mono); font-size:.72rem; color:#cfccc0;}
.av-bar-track{height:8px; background:rgba(243,240,231,.08); border-radius:6px; overflow:hidden;}
.av-bar-fill{display:block; height:100%; border-radius:6px;
  background:linear-gradient(90deg,var(--signal-deep),var(--signal));
  transform-origin:left; animation:avgrow .9s cubic-bezier(.2,.7,.2,1) both;}
.av-bar-val{font-family:var(--mono); font-size:.74rem; color:var(--fog); text-align:right;}
.av-readout-foot{margin-top:20px; padding-top:14px; border-top:1px solid var(--line);
  font-family:var(--mono); font-size:.62rem; letter-spacing:.14em; color:var(--fog2);}

/* marquee */
.av-marquee{border-top:1px solid var(--line); border-bottom:1px solid var(--line);
  overflow:hidden; padding:14px 0; margin-top:18px; -webkit-mask-image:linear-gradient(90deg,transparent,#000 12%,#000 88%,transparent);}
.av-marquee-in{display:flex; gap:34px; white-space:nowrap; width:max-content;
  animation:avmarq 24s linear infinite; font-family:var(--mono); font-size:.92rem;
  letter-spacing:.12em; color:var(--fog); text-transform:uppercase;}
.av-marquee-in i{color:var(--signal-deep); font-style:normal; margin-left:34px;}

/* shift */
.av-shift{padding:90px 0;}
.av-shift-grid{display:grid; grid-template-columns:1fr auto 1fr; gap:30px; align-items:stretch;}
@media(max-width:760px){.av-shift-grid{grid-template-columns:1fr; }.av-shift-arrow{transform:rotate(90deg);}}
.av-shift-col{border:1px solid var(--line); border-radius:14px; padding:26px;}
.av-was{opacity:.62;}
.av-now{border-color:rgba(198,240,74,.35); background:linear-gradient(180deg,rgba(198,240,74,.05),transparent);}
.av-shift-when{font-family:var(--mono); font-size:.68rem; letter-spacing:.24em; color:var(--fog);}
.av-now-when{color:var(--signal-deep);}
.av-shift-col ul{list-style:none; margin-top:16px; display:flex; flex-direction:column; gap:12px;}
.av-shift-col li{font-family:var(--serif); font-size:1.45rem; color:var(--paper); letter-spacing:-.01em;}
.av-was li{text-decoration:line-through; text-decoration-color:var(--fog2);}
.av-shift-arrow{display:flex; align-items:center; font-size:2rem; color:var(--signal);}
.av-shift-line{margin-top:34px; font-family:var(--serif); font-size:clamp(1.3rem,2.4vw,1.9rem);
  line-height:1.35; color:#cfccc0; max-width:24em;}
.av-shift-line em{color:var(--paper); font-style:italic;}

/* measure */
.av-measure{padding:30px 0 96px;}
.av-sec-head{max-width:34em; margin-bottom:42px;}
.av-sec-sub{margin-top:16px; color:var(--fog); font-size:1.05rem;}
.av-dims{display:grid; grid-template-columns:repeat(5,1fr); gap:14px;}
@media(max-width:920px){.av-dims{grid-template-columns:repeat(2,1fr);}}
@media(max-width:520px){.av-dims{grid-template-columns:1fr;}}
.av-dim{border:1px solid var(--line); border-radius:12px; padding:20px; min-height:178px;
  display:flex; flex-direction:column; transition:transform .18s,border-color .18s,background .18s;}
.av-dim:hover{transform:translateY(-4px); border-color:rgba(198,240,74,.4);
  background:linear-gradient(180deg,rgba(198,240,74,.05),transparent);}
.av-dim-top{display:flex; justify-content:space-between; align-items:center;}
.av-dim-n{font-family:var(--mono); font-size:.78rem; color:var(--signal-deep);}
.av-dim-w{font-family:var(--mono); font-size:.68rem; color:var(--fog2);
  border:1px solid var(--line); border-radius:20px; padding:2px 9px;}
.av-dim-k{font-family:var(--serif); font-weight:600; font-size:1.4rem; margin-top:20px; color:var(--paper);}
.av-dim-q{margin-top:8px; font-size:.9rem; color:var(--fog);}

/* how (light slab) */
.av-how{background:var(--paper); color:var(--ink); padding:88px 0; border-radius:30px 30px 0 0;}
.av-how-grid{display:grid; grid-template-columns:.8fr 1.2fr; gap:48px;}
@media(max-width:840px){.av-how-grid{grid-template-columns:1fr; gap:30px;}}
.av-steps{list-style:none; display:flex; flex-direction:column; gap:8px;}
.av-steps li{display:flex; gap:20px; padding:22px 0; border-top:1px solid var(--line-dk); align-items:flex-start;}
.av-steps li:last-child{border-bottom:1px solid var(--line-dk);}
.av-step-n{font-family:var(--mono); font-size:.95rem; color:#5b7d20; padding-top:3px;}
.av-steps h4{font-family:var(--serif); font-weight:600; font-size:1.4rem; letter-spacing:-.01em;}
.av-steps p{margin-top:6px; color:#55584d; font-size:.98rem; max-width:34em;}

/* proof */
.av-proof{background:var(--paper); color:var(--ink); padding:0 0 96px;}
.av-proof .av-kicker{color:#5b7d20;}
.av-stats{display:grid; grid-template-columns:repeat(3,1fr); gap:20px; margin:36px 0 40px;}
@media(max-width:680px){.av-stats{grid-template-columns:1fr;}}
.av-stat{border-top:2px solid var(--ink); padding-top:16px;}
.av-stat-n{display:block; font-family:var(--serif); font-weight:600; font-size:clamp(2.4rem,5vw,3.6rem);
  line-height:1; letter-spacing:-.02em;}
.av-stat-n i{font-style:normal; color:var(--fog2); margin:0 2px;}
.av-stat-l{display:block; margin-top:10px; font-family:var(--mono); font-size:.74rem;
  letter-spacing:.06em; color:#55584d; text-transform:uppercase;}
.av-dist{display:flex; align-items:flex-end; gap:18px; height:160px; padding:0 4px;
  border-bottom:2px solid var(--ink); margin-bottom:8px;}
.av-dist-col{flex:1; display:flex; flex-direction:column; align-items:center; height:100%; justify-content:flex-end; gap:8px;}
.av-dist-bar-wrap{flex:1; width:100%; display:flex; align-items:flex-end;}
.av-dist-bar{width:100%; border-radius:6px 6px 0 0; min-height:3px; transition:height .8s;}
.av-fill-A{background:var(--A);} .av-fill-B{background:var(--B);}
.av-fill-C{background:var(--C);} .av-fill-D{background:var(--D);} .av-fill-F{background:var(--F);}
.av-dist-g{font-family:var(--serif); font-weight:600; font-size:1.1rem;}
.av-dist-c{font-family:var(--mono); font-size:.72rem; color:#55584d;}
.av-proof-gaps{margin-top:26px; font-size:1rem; color:#55584d;}
.av-proof-gaps b{color:var(--ink);}

/* final */
.av-final{background:var(--paper); padding:0 0 30px;}
.av-final-in{background:var(--ink); border-radius:24px; padding:clamp(40px,7vw,86px) 28px; text-align:center;
  background-image:radial-gradient(80% 120% at 50% -10%,rgba(198,240,74,.12),transparent 60%);}
.av-final-h{font-family:var(--serif); font-weight:600; color:var(--paper);
  font-size:clamp(2.2rem,5.5vw,4rem); line-height:1; letter-spacing:-.02em;}
.av-final-h em{font-style:italic; color:var(--signal);}
.av-final-sub{color:var(--fog); margin:18px 0 30px; font-size:1.05rem;}
.av-field-lg{margin:0 auto; max-width:560px;}
.av-field-lg .av-input{font-size:1.05rem; padding:14px 6px;}
.av-link-lg{display:inline-block; margin-top:20px; font-family:var(--mono); font-size:.82rem;}

/* footer */
.av-foot{background:var(--paper); padding:40px 0 56px;}
.av-foot-in{display:flex; align-items:center; justify-content:space-between; gap:18px;
  flex-wrap:wrap; border-top:1px solid var(--line-dk); padding-top:28px;}
.av-foot .av-word{color:var(--ink);} .av-foot .av-logo{color:#5b7d20;}
.av-foot-mid{font-family:var(--mono); font-size:.74rem; color:#55584d; letter-spacing:.04em;}
.av-foot-r{font-family:var(--serif); font-style:italic; color:var(--ink); font-size:1.05rem;}

/* motion */
.av-rise{opacity:0; transform:translateY(22px); animation:avrise .7s cubic-bezier(.2,.7,.2,1) forwards;}
@keyframes avrise{to{opacity:1; transform:none;}}
@keyframes avgrow{from{width:0 !important;} }
@keyframes avscan{0%{transform:translateY(-90px);}100%{transform:translateY(560px); opacity:0;}}
@keyframes avpop{from{opacity:0; transform:scale(.6) rotate(-8deg);}to{opacity:1; transform:none;}}
@keyframes avpulse{0%,100%{opacity:1;}50%{opacity:.35;}}
@keyframes avmarq{to{transform:translateX(-33.33%);}}
@media(prefers-reduced-motion:reduce){
  .av-rise,.av-grade,.av-bar-fill{animation:none !important; opacity:1 !important; transform:none !important; width:var(--w,auto);}
  .av-scan,.av-marquee-in{animation:none !important;}
}
`;
