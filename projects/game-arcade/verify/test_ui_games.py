# encoding: utf-8
from playwright.sync_api import expect

# Auto-retrying waits: both lists are filled by a client-side fetch after
# navigation, and Locator.count() returns immediately without waiting.
UI_TIMEOUT = 15_000

def test_c_4_2_games_list_renders_one_row_per_game(page, base_url: str, http_client):
    # Create two games via API so the list has content.
    g1 = http_client.post("/api/games", json={"seed": 4001}).json()
    g2 = http_client.post("/api/games", json={"seed": 4002}).json()
    # Add differing numbers of guesses so guessCount can display.
    http_client.post(f"/api/games/{g1['id']}/guesses", json={"code": [0, 1, 2, 3]})
    http_client.post(f"/api/games/{g2['id']}/guesses", json={"code": [4, 5, 0, 1]})
    http_client.post(f"/api/games/{g2['id']}/guesses", json={"code": [1, 1, 1, 1]})

    page.goto(base_url + "/games")
    # Expect exactly two rows once the client-side fetch has resolved.
    rows = page.locator('[data-testid="game-row"]')
    expect(rows).to_have_count(2, timeout=UI_TIMEOUT)


def test_c_4_3_resume_navigates_to_board_with_correct_guess_rows(page, base_url: str, http_client):
    # Prepare a game with k guesses
    k = 3
    game = http_client.post("/api/games", json={"seed": 4003}).json()
    for code in ([0, 0, 0, 0], [1, 2, 3, 4], [2, 2, 2, 2]):
        http_client.post(f"/api/games/{game['id']}/guesses", json={"code": code})

    # Open the games list and click Resume for this game.
    page.goto(base_url + "/games")
    page.get_by_test_id(f"resume-{game['id']}").click()
    # Expect k rows on the board.
    rows = page.locator('[data-testid^="guess-row-"]')
    expect(rows).to_have_count(k, timeout=UI_TIMEOUT)
