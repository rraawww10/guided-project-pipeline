# -*- coding: utf-8 -*-
from urllib.parse import urlparse

from playwright.sync_api import Page, TimeoutError as PWTimeout
import httpx

from .utils import create_game, post_guess, poll_guesses_len


def test_c_1_3_ui_submit_creates_one_guess_row(client: httpx.Client, page: Page):
    # Drive the board to submit a first guess. The spec names a Submit button; colours are not pinned,
    # so we click Submit and then verify via the API that one guess was created.
    game_id, _ = create_game(client, seed=12)
    page.goto(f"/game/{game_id}")
    # Try clicking a button labelled Submit
    try:
        page.get_by_text("Submit", exact=True).click(timeout=1500)
    except PWTimeout:
        # Fall back to clicking any button with text containing Submit
        page.locator("button:has-text('Submit')").first.click(timeout=1500)
    # Verify a guess exists for this game via the API
    game = poll_guesses_len(client, game_id, expected=1, timeout_s=3.0)
    last = game["guesses"][0]
    assert isinstance(last.get("code"), list) and len(last["code"]) == 4, f"first guess must have 4-code, got {last}"


def test_c_2_4_feedback_pegs_match_stored_counts(client: httpx.Client, page: Page):
    # Post a known-scored guess (black=4 white=0) then assert the row renders that feedback.
    # Selectors for pegs are not pinned; this test assumes accessible labels 'black peg' and 'white peg'.
    # If the UI uses a different hook, pin it in the spec or mirror these a11y labels.
    game_id, _ = create_game(client, seed=726)  # secret [0,1,2,3]
    post_guess(client, game_id, [0, 1, 2, 3])

    page.goto(f"/game/{game_id}")
    # Count feedback pegs on the most recent row; be tolerant on timing.
    page.wait_for_timeout(300)  # allow render
    blacks = page.locator("[aria-label='black peg']").count()
    whites = page.locator("[aria-label='white peg']").count()
    assert blacks == 4 and whites == 0, f"expected 4 black, 0 white pegs, got black={blacks} white={whites}"


essay = """
NOTE: Tests c-2-5 and c-4-3 rely on counting visible guess rows on the board. The spec does not pin
stable hooks for rows, so these tests use generic list markup assumptions. If the UI uses a different
structure, add a stable data-testid on each guess row and adjust these selectors in a follow-up.
"""


def _max_list_len(page: Page) -> int:
    # Heuristic: the guesses are often rendered as a list; measure the longest UL's LI count.
    counts = []
    for i in range(page.locator("ul").count()):
        ul = page.locator("ul").nth(i)
        counts.append(ul.locator("li").count())
    return max(counts) if counts else 0


def test_c_2_5_two_submissions_render_two_rows(client: httpx.Client, page: Page):
    game_id, _ = create_game(client, seed=12)
    post_guess(client, game_id, [0, 0, 0, 0])
    post_guess(client, game_id, [1, 1, 1, 1])

    page.goto(f"/game/{game_id}")
    page.wait_for_timeout(300)
    rows = _max_list_len(page)
    assert rows == 2, f"expected two visible rows, got {rows}"


def test_c_3_4_hint_text_shows_expected_remaining_after_zero_score(client: httpx.Client, page: Page):
    # Seed whose secret has no zeroes so [0,0,0,0] scores 0/0, and the next hint is 1 1 1 1 with 625 left.
    seed = 259  # [1,1,1,1]
    game_id, _ = create_game(client, seed=seed)
    post_guess(client, game_id, [0, 0, 0, 0])

    page.goto(f"/game/{game_id}")
    locator = page.locator("text=Hint: 1 1 1 1 • Remaining 625")
    page.wait_for_selector("text=Hint: 1 1 1 1 • Remaining 625", timeout=2000)
    assert locator.count() >= 1, "expected hint text to be visible"


def test_c_4_3_turn_control_limits_rows_to_k(client: httpx.Client, page: Page):
    # Create a 3-guess game
    game_id, _ = create_game(client, seed=12)
    post_guess(client, game_id, [0, 0, 0, 0])
    post_guess(client, game_id, [1, 1, 1, 1])
    post_guess(client, game_id, [2, 2, 2, 2])

    page.goto(f"/game/{game_id}")
    page.wait_for_timeout(200)
    # Find a Turn control; assume it's a range input and set it to 2
    slider = page.locator("input[type='range']").first
    slider.fill("2")
    page.wait_for_timeout(200)
    rows = _max_list_len(page)
    assert rows == 2, f"after moving Turn to 2, expected 2 visible rows, got {rows}"


def test_c_4_4_branch_from_turn_k_creates_new_game_with_prefix(client: httpx.Client, page: Page):
    # Prepare a game with two guesses, then branch from turn 1 and verify the new game's guesses equal 1.
    game_id, _ = create_game(client, seed=35)
    post_guess(client, game_id, [0, 0, 0, 0])
    post_guess(client, game_id, [1, 1, 1, 1])

    page.goto(f"/game/{game_id}")
    # Click the pinned text 'Branch from turn 1'
    page.get_by_text("Branch from turn 1").click()
    # After navigation, URL should contain /game/<newid>
    page.wait_for_url("**/game/*", timeout=2000)
    new_path = urlparse(page.url).path
    assert new_path.startswith("/game/"), f"expected to be on a game page, got {page.url}"
    new_id = new_path.rsplit("/", 1)[-1]

    # Verify the branched game has exactly 1 guess via API
    r = client.get(f"/api/games/{new_id}")
    assert r.status_code == 200, f"branched game should exist, got {r.status_code}: {r.text}"
    guesses = (r.json().get("guesses") or [])
    assert len(guesses) == 1, f"branched game should replay first K guesses (K=1), got {len(guesses)}"
