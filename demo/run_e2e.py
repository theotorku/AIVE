"""E2E demo capture: landing -> live audit -> grade teaser, plus the sample report.

Records the browser session to demo/video/ and writes step screenshots to demo/.
Servers (backend :8000, frontend :5173) are started by with_server.py.
"""

from __future__ import annotations

import pathlib
import time

from playwright.sync_api import sync_playwright

TARGET_URL = "www.dallasheatingac.com"
BASE = "http://localhost:5173"
OUT = pathlib.Path(__file__).resolve().parent
VIDEO_DIR = OUT / "video"
AUDIT_TIMEOUT_S = 360  # live crawl + per-page LLM can take a couple of minutes

OUT.mkdir(exist_ok=True)
VIDEO_DIR.mkdir(exist_ok=True)


def shot(page, name: str, full_page: bool = False) -> None:
    path = OUT / name
    page.screenshot(path=str(path), full_page=full_page)
    print(f"  screenshot -> {path.name}")


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1440, "height": 900},
        )
        page = context.new_page()
        page.on("console", lambda m: print(f"  [console.{m.type}] {m.text}"))

        print("1) landing page")
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)
        shot(page, "01-landing.png")
        shot(page, "01-landing-full.png", full_page=True)

        print(f"2) submit {TARGET_URL}")
        hero_input = page.locator(".hero .url-capture input")
        hero_input.fill(TARGET_URL)
        page.wait_for_timeout(300)
        shot(page, "02-url-entered.png")
        page.locator(".hero .url-capture button").click()

        print("3) audit running overlay")
        page.wait_for_selector(".audit-overlay", timeout=15_000)
        page.wait_for_timeout(1500)
        shot(page, "03-auditing.png")

        print("4) waiting for grade teaser (live crawl + scoring)...")
        deadline = time.time() + AUDIT_TIMEOUT_S
        result_state = None
        while time.time() < deadline:
            if page.locator(".audit-result").count() > 0:
                result_state = "teaser"
                break
            if page.locator(".audit-running .eyebrow").count() > 0:
                txt = page.locator(".audit-running .eyebrow").inner_text()
                if "failed" in txt.lower():
                    result_state = "error"
                    break
            page.wait_for_timeout(2000)

        if result_state == "teaser":
            print("   grade teaser rendered")
            page.wait_for_timeout(800)
            shot(page, "04-grade-teaser.png")
            grade = page.locator(".audit-letter").inner_text()
            score = page.locator(".audit-score").inner_text()
            print(f"   GRADE={grade}  {score}")
        elif result_state == "error":
            print("   audit reported an error")
            shot(page, "04-audit-error.png")
        else:
            print("   timed out waiting for teaser")
            shot(page, "04-timeout.png")

        print("5) public sample report")
        page.goto(f"{BASE}/?report=sample")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("text=AI Visibility Report", timeout=15_000)
        page.wait_for_timeout(1500)
        shot(page, "05-sample-report.png")
        shot(page, "05-sample-report-full.png", full_page=True)

        video_path = page.video.path() if page.video else None
        context.close()  # finalizes the video file
        browser.close()
        if video_path:
            print(f"video -> {video_path}")


if __name__ == "__main__":
    main()
