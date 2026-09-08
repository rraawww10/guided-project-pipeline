# encoding: utf-8
import re
import json
from typing import List

from playwright.sync_api import expect

from verify.helpers import derive_secret

# Auto-retrying waits: a fixed sleep races the client-side fetch that fills
# these lists, and Locator.count() does not wait at all.
UI_TIMEOUT = 15_000


def _ui_new_game(page, base_url: str, seed: int) -> None:
    page.goto(base_url + "/")
    page.get_by_test_id("seed-input").fill(str(seed))
    page.get_by_test_id("new-game").click()
    # createGame() is async: it awaits POST /api/games, clears any pending picks,
    # then routes to /?game=<id>. Returning before that lands means the colour
    # clicks below are wiped by its own reset and the guess is never submitted.
    page.wait_for_url(re.compile(r"[?&]game="), timeout=UI_TIMEOUT)


def _ui_pick_code(page, code: List[int]) -> None:
    # Click four picker buttons; the app should place them into slots 0..3
    for v in code:
        page.get_by_test_id(f"picker-color-{v}").click()


def _ui_submit_guess(page) -> None:
    page.get_by_test_id("submit-guess").click()


def _guess_rows(page):
    return page.locator('[data-testid^="guess-row-"]')


def _expect_guess_rows(page, n: int) -> None:
    expect(_guess_rows(page)).to_have_count(n, timeout=UI_TIMEOUT)


# Session 1 UI

def test_c_1_3_submit_one_guess_renders_exactly_one_row(page, base_url: str):
    seed = 3001

    # Install a strict network gate BEFORE creating the game so any fallback
    # re-read path cannot populate rows. We only allow GET /api/games/:id calls
    # and force them to return an empty guesses array; everything else continues.
    # Which games were re-read, not merely whether any were. The seed holds a
    # fixture game (seed-game-1) for c-2-1's benefit, and a page that reads
    # some OTHER game is not the defect this guards against - papering over a
    # missing client append by re-reading THE GAME UNDER TEST is.
    refetched: List[str] = []
    seen_refetch = {"seen": False}

    def handle(route, request):
        url = request.url
        # Intercept any GET to /api/games/<id> (but not /api/games or /hint)
        if request.method == "GET" and re.search(r"/api/games/[^/]+(?:[/?#]|$)", url):
            seen_refetch["seen"] = True
            # Extract an id-shaped suffix to echo back; fall back to a stub.
            m = re.search(r"/api/games/([^/?#]+)", url)
            gid = m.group(1) if m else "stub"
            refetched.append(gid)
            # Always answer with an empty guess list so only the client append
            # can produce a visible row.
            body = json.dumps({"id": gid, "seed": seed, "guesses": []})
            route.fulfill(status=200, content_type="application/json", body=body)
        else:
            route.continue_()

    page.route("**/api/games/**", handle)

    _ui_new_game(page, base_url, seed)
    # Capture the created game id from the URL (sanity check only).
    m = re.search(r"[?&]game=([^&#]+)", page.url)
    assert m, "game id not found in URL after New Game"

    code = [0, 1, 2, 3]
    _ui_pick_code(page, code)
    _ui_submit_guess(page)

    # Assert exactly one prior guess row renders, driven by the client append.
    _expect_guess_rows(page, 1)
    # And the row shows the four chosen values in its slots.
    row = _guess_rows(page).nth(0)
    for i, v in enumerate(code):
        txt = row.get_by_test_id(f"slot-{i}").inner_text().strip()
        assert txt == str(v)

    # Guardrail: the UI must NOT have re-fetched the game to populate the row.
    # This makes the test fail if an implementation papers over the missing
    # client append by re-reading from the server.
    game_id = m.group(1)
    assert game_id not in refetched, (
        f"UI re-fetched /api/games/{game_id}; the row must come from the client "
        f"append. Games read during this test: {refetched}")


# Session 2 UI

def test_c_2_5_row_shows_black_and_white_counts_matching_secret(page, base_url: str):
    # Choose a seed and compute its secret, then submit that exact guess.
    seed = 3002
    secret = derive_secret(seed)
    _ui_new_game(page, base_url, seed)
    _ui_pick_code(page, secret)
    _ui_submit_guess(page)
    # Expect black=4 and white=0 shown in their testids
    _expect_guess_rows(page, 1)
    blk = page.get_by_test_id("score-black").inner_text().strip()
    wht = page.get_by_test_id("score-white").inner_text().strip()
    assert blk == "4"
    assert wht == "0"


# Session 3 UI

def test_c_3_3_page_shows_hint_remaining_and_suggestion(page, base_url: str):
    # New game, no guesses yet.
    seed = 3003
    _ui_new_game(page, base_url, seed)
    # Expect hint remaining and suggestion elements to exist with expected values.
    page.wait_for_selector('[data-testid="hint-remaining"]')
    remaining_text = page.get_by_test_id("hint-remaining").inner_text().strip()
    suggestion_text = page.get_by_test_id("hint-suggestion").inner_text().strip()
    assert remaining_text == "1296"
    # Allow any reasonable formatting; ensure it conveys four zeros.
    zeros = re.findall(r"0", suggestion_text)
    assert len(zeros) == 4


# Session 4 UI

def test_c_4_5_branch_here_button_renders_k_rows(page, base_url: str, http_client):
    # Prepare a game with three guesses via API, then resume it in UI and branch at k=2.
    src = http_client.post("/api/games", json={"seed": 3004}).json()
    for code in ([0, 1, 2, 3], [1, 2, 3, 4], [2, 3, 4, 5]):
        http_client.post(f"/api/games/{src['id']}/guesses", json={"code": code})

    # Go through /games to pick the game (exercise the intended navigation path).
    page.goto(base_url + "/games")
    page.get_by_test_id(f"resume-{src['id']}").click()
    # Click Branch Here on row k=2 (two rows should remain)
    page.get_by_test_id("branch-here-2").click()
    # After branching, the board reloads to exactly k rows.
    _expect_guess_rows(page, 2)
