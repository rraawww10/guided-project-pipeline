# encoding: utf-8
from typing import List, Tuple

from verify.helpers import derive_secret, score_guess, all_codes


def test_c_3_1_hint_no_guesses_remaining_1296_and_suggestion_zeros(http_client):
    seed = 112233
    game = http_client.post("/api/games", json={"seed": seed}).json()
    res = http_client.get(f"/api/games/{game['id']}/hint")
    assert res.status_code == 200
    body = res.json()
    assert body.get("remaining") == 1296
    assert body.get("suggestion") == [0, 0, 0, 0]


def test_c_3_2_hint_remaining_matches_consistent_set_for_one_guess(http_client):
    seed = 221144
    game = http_client.post("/api/games", json={"seed": seed}).json()
    secret = derive_secret(seed)
    # Choose a non-trivial guess (not equal to secret); tweak if needed.
    guess = [0, 1, 2, 3]
    if guess == secret:
        guess = [0, 1, 2, 4]
    # Record the guess so the server has a history.
    r = http_client.post(f"/api/games/{game['id']}/guesses", json={"code": guess})
    assert r.status_code == 201
    b, w = score_guess(secret, guess)

    # Ask for the hint and compare remaining against a local filter of the space.
    res = http_client.get(f"/api/games/{game['id']}/hint")
    assert res.status_code == 200
    body = res.json()
    # Locally compute candidates: codes whose score against this guess equals (b,w)
    space = all_codes()
    expected_remaining = sum(1 for code in space if score_guess(code, guess) == (b, w))
    assert body.get("remaining") == expected_remaining


def test_c_3_4_two_games_identical_histories_same_suggestion(http_client):
    # Use the same seed and the same recorded guess so histories match.
    seed = 54321
    g1 = http_client.post("/api/games", json={"seed": seed}).json()
    g2 = http_client.post("/api/games", json={"seed": seed}).json()
    # Record the same guess in both
    guess = [1, 2, 3, 4]
    http_client.post(f"/api/games/{g1['id']}/guesses", json={"code": guess})
    http_client.post(f"/api/games/{g2['id']}/guesses", json={"code": guess})

    h1 = http_client.get(f"/api/games/{g1['id']}/hint").json()
    h2 = http_client.get(f"/api/games/{g2['id']}/hint").json()
    assert h1.get("suggestion") == h2.get("suggestion")
