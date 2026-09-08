import os
from pathlib import Path
import json
import pytest
from playwright.sync_api import sync_playwright, expect


@pytest.fixture(autouse=True)
def reset_state_file():
    """Restore data/state.json from data/state.seed.json before every test.

    If the seed file is absent, skip the reset silently so targets that never
    had one behave as before (see Test Writer skill guidance).
    """
    app_dir = Path(os.environ.get("APP_DIR", os.getcwd()))
    data_dir = app_dir / "data"
    seed = data_dir / "state.seed.json"
    live = data_dir / "state.json"
    if seed.exists():
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            live.write_text(seed.read_text())
        except Exception:
            # Do not fail collection/reset on IO issues in red-first; tests will
            # surface functional faults when the app exists.
            pass
    yield


@pytest.fixture(scope="session")
def base_url() -> str:
    url = os.environ.get("BASE_URL")
    assert url, "BASE_URL is not set; the test runner should provide it"
    return url


@pytest.fixture()
def page(base_url: str):
    """Provide a fresh Playwright page per test.

    Do not rely on any shared browser or page: each test gets its own context.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(base_url=base_url)
        pg = context.new_page()
        try:
            yield pg
        finally:
            context.close()
            browser.close()


@pytest.fixture()
def http_client(base_url: str):
    import httpx
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        yield client
