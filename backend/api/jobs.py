"""Background pipeline runs for the dashboard.

A live URL submission can take minutes (crawl + per-page LLM), so each run
executes on a worker thread and the UI polls its status. Status stages come
straight from the pipeline's progress hook — no faked progress.
"""

from __future__ import annotations

import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from backend.crawler.crawl import _domain_slug, _normalize_url
from backend.app.pipeline import run_pipeline
from backend.api import store

logger = logging.getLogger(__name__)

# queued -> crawling -> extracting -> scoring -> done | error
STAGES = ["queued", "crawling", "extracting", "scoring", "done"]

# Shown to the client when an unexpected exception aborts a run. The real
# traceback is logged server-side; internals (paths, module names, stack) must
# never reach the UI.
_GENERIC_ERROR = "The audit failed unexpectedly. Please try again later."


@dataclass
class Job:
    run_id: str
    url: str
    domain: str
    status: str = "queued"      # queued | running | done | error
    stage: str = "queued"       # finer-grained progress
    error: str | None = None
    domain_ready: bool = False  # whether artifacts exist for the domain

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id, "url": self.url, "domain": self.domain,
            "status": self.status, "stage": self.stage, "error": self.error,
            "domain_ready": self.domain_ready,
        }


class JobManager:
    def __init__(self, max_workers: int = 2):
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def submit(self, url: str) -> Job:
        norm = _normalize_url(url)
        domain = _domain_slug(norm)
        run_id = uuid.uuid4().hex[:12]
        job = Job(run_id=run_id, url=norm, domain=domain)
        with self._lock:
            self._jobs[run_id] = job
        self._pool.submit(self._run, job)
        return job

    def get(self, run_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(run_id)

    def _run(self, job: Job) -> None:
        job.status = "running"

        def progress(stage: str) -> None:
            job.stage = stage

        try:
            # reuse_crawl=True: if we've crawled this domain before, skip the
            # browser; otherwise crawl live. Always re-runs extraction + scoring.
            result = run_pipeline(job.url, output_root=str(store.OUTPUT_DIR),
                                  reuse_crawl=True, progress=progress)
            if result.error:
                job.status, job.error, job.stage = "error", result.error, "error"
                return
            job.domain = result.domain
            job.domain_ready = store.has_profile(result.domain)
            job.status, job.stage = "done", "done"
        except Exception:  # noqa: BLE001
            # Log the full detail for operators; surface only a generic message.
            logger.exception("Pipeline run %s failed for %s", job.run_id, job.url)
            job.status = "error"
            job.stage = "error"
            job.error = _GENERIC_ERROR


manager = JobManager()
