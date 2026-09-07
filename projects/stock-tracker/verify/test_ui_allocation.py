import os
import time
from playwright.sync_api import sync_playwright


def _base_url() -> str:
    url = os.environ.get("BASE_URL")
    assert url, "BASE_URL is not set"
    return url.rstrip("/")


def test_c_2_2_ui_shows_over_badge_for_overweight():
    base = _base_url()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base + "/")
        page.wait_for_selector('[data-testid^="drift-"]', timeout=5000)
        labels = [el.inner_text().strip() for el in page.locator('[data-testid^="drift-"]').all()]
        assert any(lbl == "OVER" for lbl in labels)
        browser.close()


def test_c_2_3_ui_shows_under_badge_for_underweight():
    base = _base_url()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base + "/")
        page.wait_for_selector('[data-testid^="drift-"]', timeout=5000)
        labels = [el.inner_text().strip() for el in page.locator('[data-testid^="drift-"]').all()]
        assert any(lbl == "UNDER" for lbl in labels)
        browser.close()


def test_c_2_4_ui_shows_loading_text_while_fetching():
    """c-2-4: the loading text shows *while* fetching - so it must also stop.

    Asserting only that "Loading..." appears passes on the skeleton and is
    therefore no test at all. `{!reportState && <div>Loading...</div>}` sits
    outside cut-ui-fetch-allocation, so it survives the cut, and with the fetch
    removed `reportState` is never set and the text is permanent - the fallback
    accidentally satisfying the criterion (lessons.md). The transition is the
    part only a real fetch can produce.

    The response is held open first so the appearance cannot be raced against
    local SQLite, then released so the disappearance is a real resolution.
    """
    base = _base_url()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        held = {"once": False}

        def _hold(route):
            if not held["once"]:
                held["once"] = True
                time.sleep(1.5)
            route.continue_()

        page.route("**/api/allocation*", _hold)
        page.goto(base + "/", wait_until="commit")
        page.wait_for_selector("text=Loading...", timeout=15000)
        # The report itself has to arrive. This is the half the skeleton cannot
        # satisfy: reportState is only set by the fetch inside
        # cut-ui-fetch-allocation, and line 96 renders the drift container only
        # when it is set. Measured on the skeleton - the SSR html carries
        # "Loading..." and React drops it at hydration, so appear-then-clear
        # alone passed there on a page that never fetched anything.
        page.wait_for_selector('[data-testid^="drift-"]', timeout=20000)
        page.wait_for_selector("text=Loading...", state="detached", timeout=20000)
        browser.close()
