// Typed client for the ABI Dashboard API. Types mirror the real pipeline
// artifacts (profile.json / abi_score.json); nothing here is mocked.

export interface SiteSummary {
  domain: string;
  business_name: string | null;
  industry: string | null;
  overall: number | null;
  grade: string | null;
  grade_label: string | null;
}

export interface Criterion {
  name: string;
  earned: number;
  max: number;
  ratio: number;
  rationale: string;
  evidence: string[];
  recommendation: string | null;
}

export interface Dimension {
  label: string;
  score: number;
  weight: number;
  grade: string;
  criteria: Criterion[];
}

export interface Recommendation {
  dimension: string;
  dimension_label: string;
  criterion: string;
  recommendation: string;
  impact: number;
  priority: number;
}

export interface AbiScore {
  overall: number;
  grade: string;
  grade_label: string;
  dimensions: Record<string, Dimension>;
  top_recommendations: Recommendation[];
  summary: string;
  weights: Record<string, number>;
}

export interface EvidenceItem {
  value: string;
  confidence: number;
  evidence?: string;
  source_url?: string;
  confidence_reason?: string;
  [k: string]: unknown;
}

export interface Profile {
  business_name: string | null;
  industry: string | null;
  services: EvidenceItem[];
  service_areas: EvidenceItem[];
  locations: EvidenceItem[];
  faqs: EvidenceItem[];
  offers: EvidenceItem[];
  trust_signals: EvidenceItem[];
  ctas: EvidenceItem[];
  contact_information: Record<string, string | null>;
  structured_data?: Record<string, boolean>;
  source_pages: { url: string; category: string }[];
}

export interface CrawlCoverage {
  final_page_count?: number;
  meaningful_pages_found?: number;
  sitemap_url_count?: number;
  canonical_host?: string;
  low_coverage?: boolean;
  warning?: string | null;
  crawled_urls?: { url: string; link_source?: string; depth?: number; ok?: boolean; error?: string }[];
  skipped_urls?: { url: string; reason: string }[];
}

export interface SiteDetail {
  domain: string;
  profile: Profile;
  abi_score: AbiScore | null;
  pipeline: Record<string, unknown>;
  confidence: { average_confidence?: number };
  coverage?: CrawlCoverage;
}

export interface Job {
  run_id: string;
  url: string;
  domain: string;
  status: "queued" | "running" | "done" | "error";
  stage: string;
  error: string | null;
  domain_ready: boolean;
}

export interface Benchmark {
  sites_scored: number;
  benchmark: {
    average_abi: number;
    lowest_abi: number;
    highest_abi: number;
    component_averages: Record<string, number>;
    grade_distribution: Record<string, number>;
    common_weaknesses: [string, number][];
  };
}

async function get<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

export const api = {
  sites: () => get<{ sites: SiteSummary[] }>("/api/sites").then((d) => d.sites),
  site: (domain: string) => get<SiteDetail>(`/api/sites/${domain}`),
  benchmark: () => get<Benchmark>("/api/benchmark"),
  reportUrl: (domain: string) => `/api/sites/${domain}/report`,
  startRun: async (url: string): Promise<Job> => {
    const r = await fetch("/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json();
  },
  run: (runId: string) => get<Job>(`/api/runs/${runId}`),
};

export const GRADE_COLOR: Record<string, string> = {
  A: "green.500",
  B: "green.400",
  C: "yellow.500",
  D: "orange.500",
  F: "red.500",
};

// Plain-language layer (UI only — does not touch the frozen ABI framework).
// Translates the five dimension keys into something a non-technical business
// owner understands at a glance.
export const DIMENSION_PLAIN: Record<string, { short: string; question: string }> = {
  ai_understanding: { short: "Understanding", question: "Can AI tell what your business does?" },
  ai_retrieval: { short: "Findability", question: "Can AI find and pull up your content?" },
  ai_recommendation: { short: "Trust", question: "Will AI feel confident recommending you?" },
  agent_readiness: { short: "Action-ready", question: "Can an AI assistant book or contact you?" },
  semantic_authority: { short: "Authority", question: "Does AI see you as a credible source?" },
};

// What the headline grade means, in one plain sentence.
export const GRADE_MEANING: Record<string, string> = {
  A: "AI understands your business very well and is likely to surface it.",
  B: "AI understands your business well, with a few gaps to close.",
  C: "AI only partially understands your business.",
  D: "AI struggles to understand your business — important details are missing.",
  F: "AI can barely understand your business right now.",
};
