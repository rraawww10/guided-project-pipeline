# encoding: utf-8
import json
from typing import List

import pytest

from verify.helpers import derive_secret, score_guess, find_seed_with_distinct_secret


# Session 1

def test_c_1_1_post_games_creates_and_echoes_seed(http_client):
    seed = 123456
    res = http_client.post("/api/games", json={"seed": seed})
    assert res.status_code == 201, f"expected 201, got {res.status_code}: {res.text}"
    body = res.json()
    assert isinstance(body.get("id"), str) and len(body["id"]) > 0
    assert body.get("seed") == seed


def test_c_1_2_post_guess_persists_code_black_white_unscored_or_present(http_client):
    # Note: The spec's session-1 text says black/white are null (no scoring yet),
    # but session 2 adds scoring to the same endpoint. We assert invariants that
    # survive both: code is echoed and black/white fields are present (nullable or numeric).
    seed = 24680
    game = http_client.post("/api/games", json={"seed": seed}).json()
    code = [0, 1, 2, 3]
    res = http_client.post(f"/api/games/{game['id']}/guesses", json={"code": code})
    assert res.status_code == 201, f"expected 201, got {res.status_code}: {res.text}"
    body = res.json()
    assert body.get("code") == code
    # Presence and type tolerance: before scoring they may be null; afterwards numbers.
    assert "black" in body and (body["black"] is None or isinstance(body["black"], int))
    assert "white" in body and (body["white"] is None or isinstance(body["white"], int))


# Session 2

def test_c_2_1_get_game_returns_seed_and_empty_guesses_for_new_game(http_client):
    seed = 13579
    game = http_client.post("/api/games", json={"seed": seed}).json()
    res = http_client.get(f"/api/games/{game['id']}")
    assert res.status_code == 200
    body = res.json()
    assert body.get("id") == game["id"]
    assert body.get("seed") == seed
    assert isinstance(body.get("guesses"), list) and len(body["guesses"]) == 0


def test_c_2_2_post_guess_equal_to_secret_returns_black4_white0(http_client):
    # Choose a seed and compute its secret per spec's xorshift32.
    seed = 778899
    game = http_client.post("/api/games", json={"seed": seed}).json()
    secret = derive_secret(seed)
    res = http_client.post(f"/api/games/{game['id']}/guesses", json={"code": secret})
    assert res.status_code == 201
    body = res.json()
    assert body.get("black") == 4
    assert body.get("white") == 0


def test_c_2_3_permuted_all_colours_black0_white4(http_client):
    # Find a seed whose secret has 4 distinct colours so a derangement exists.
    seed, secret = find_seed_with_distinct_secret(start=4242)
    game = http_client.post("/api/games", json={"seed": seed}).json()
    # A simple rotation is a derangement when all values are distinct.
    guess = [secret[1], secret[2], secret[3], secret[0]]
    res = http_client.post(f"/api/games/{game['id']}/guesses", json={"code": guess})
    assert res.status_code == 201
    body = res.json()
    assert body.get("black") == 0
    assert body.get("white") == 4


def test_c_2_4_get_game_returns_guesses_with_numeric_scores(http_client):
    seed = 97531
    game = http_client.post("/api/games", json={"seed": seed}).json()
    secret = derive_secret(seed)
    # Make two guesses: one equal to secret and one permuted/all-colours if possible
    g1 = secret
    http_client.post(f"/api/games/{game['id']}/guesses", json={"code": g1})
    # Second guess: flip first two positions; may reduce blacks
    g2 = [secret[1], secret[0], secret[2], secret[3]]
    http_client.post(f"/api/games/{game['id']}/guesses", json={"code": g2})

    res = http_client.get(f"/api/games/{game['id']}")
    assert res.status_code == 200
    body = res.json()
    guesses = body.get("guesses")
    assert isinstance(guesses, list) and len(guesses) >= 2
    # Check scores are numeric and match the scoring function
    seen = 0
    for g in guesses:
        if g.get("code") in (g1, g2):
            b, w = score_guess(secret, g["code"])  # type: ignore[arg-type]
            assert isinstance(g.get("black"), int) and isinstance(g.get("white"), int)
            assert g.get("black") == b and g.get("white") == w
            seen += 1
    assert seen == 2
