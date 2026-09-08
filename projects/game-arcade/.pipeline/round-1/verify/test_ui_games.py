# -*- coding: utf-8 -*-
from playwright.sync_api import Page
import httpx

from .utils import create_game, post_guess


def test_c_4_2_games_list_renders_rows_and_resume_navigates(client: httpx.Client, page: Page):
    # Create a game with one guess so guessCount > 0 and the id appears in the list
    gid, _ = create_game(client, seed=99)
    post_guess(client, gid, [0, 0, 0, 0])

    page.goto("/games")
    # Find a row containing the game id and click it to resume
    page.get_by_text(gid).click()
    page.wait_for_url(f"**/game/{gid}", timeout=2000)
    assert page.url.endswith(f"/game/{gid}")
