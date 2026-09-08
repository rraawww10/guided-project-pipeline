# -*- coding: utf-8 -*-
import httpx

from .utils import create_game, get_hint, post_guess


def test_c_3_1_hint_remaining_1296_no_guesses(client: httpx.Client):
    game_id, _ = create_game(client, seed=13)
    hint = get_hint(client, game_id)
    assert hint.get("remaining") == 1296, f"expected remaining 1296 with no guesses, got {hint}"


def test_c_3_2_hint_suggests_zeros_initially(client: httpx.Client):
    game_id, _ = create_game(client, seed=5)
    hint = get_hint(client, game_id)
    assert hint.get("suggested") == [0, 0, 0, 0], f"expected suggested [0,0,0,0], got {hint}"


def test_c_3_3_hint_remaining_625_after_zero_score_guess(client: httpx.Client):
    # Pick a seed whose secret has no zeroes so [0,0,0,0] yields 0 black, 0 white
    seed = 259  # digits [1,1,1,1]
    game_id, _ = create_game(client, seed=seed)
    post_guess(client, game_id, [0, 0, 0, 0])
    hint = get_hint(client, game_id)
    assert hint.get("remaining") == 625, f"expected remaining 625 after eliminating all codes containing 0, got {hint}"
