# -*- coding: utf-8 -*-
import httpx

from .utils import create_game, get_game, post_guess, secret_from_seed, rotate_right


def test_c_2_1_exact_secret_scores_black4_white0(client: httpx.Client):
    # Choose a seed with distinct digits 0,1,2,3 for clarity
    seed = 726  # digits [0,1,2,3]
    game_id, used_seed = create_game(client, seed=seed)
    secret = secret_from_seed(used_seed)
    post_guess(client, game_id, secret)
    data = get_game(client, game_id)
    last = data["guesses"][-1]
    assert last.get("black") == 4 and last.get("white") == 0, f"expected black=4 white=0, got {last}"


def test_c_2_2_rotation_scores_black0_white4(client: httpx.Client):
    seed = 726  # digits [0,1,2,3]
    game_id, used_seed = create_game(client, seed=seed)
    secret = secret_from_seed(used_seed)
    rotated = rotate_right(secret)
    assert all(a != b for a, b in zip(secret, rotated)), "rotation should avoid positional matches"
    post_guess(client, game_id, rotated)
    data = get_game(client, game_id)
    last = data["guesses"][-1]
    assert last.get("black") == 0 and last.get("white") == 4, f"expected black=0 white=4, got {last}"


def test_c_2_3_repeats_no_double_counting_sum_matches(client: httpx.Client):
    # Secret with repeats: [1,1,2,3]
    seed = 727  # 3*6^3 + 2*6^2 + 1*6 + 1
    game_id, _ = create_game(client, seed=seed)
    # Guess arranged to force no double counting: [1,2,1,4]
    guess = [1, 2, 1, 4]
    post_guess(client, game_id, guess)
    data = get_game(client, game_id)
    last = data["guesses"][-1]
    black = int(last.get("black", -1))
    white = int(last.get("white", -1))
    assert black + white == 3, f"expected total matches 3 with no double counting, got black={black} white={white} ({last})"
