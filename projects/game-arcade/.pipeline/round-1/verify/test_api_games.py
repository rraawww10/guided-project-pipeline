# -*- coding: utf-8 -*-
import httpx

from .utils import create_game, get_game, post_guess


def test_c_1_1_post_games_returns_201_with_id_and_seed(client: httpx.Client):
    r = client.post("/api/games", json={})
    assert r.status_code == 201, f"expected 201, got {r.status_code}: {r.text}"
    data = r.json()
    assert isinstance(data.get("id"), str), f"id must be a string, got {data}"
    assert isinstance(data.get("seed"), int), f"seed must be a number, got {data}"


def test_c_1_2_get_game_returns_empty_guesses_initially(client: httpx.Client):
    game_id, _ = create_game(client)
    data = get_game(client, game_id)
    assert "guesses" in data, f"response must include guesses array: {data}"
    assert isinstance(data["guesses"], list), f"guesses must be a list, got {type(data['guesses'])}"
    assert len(data["guesses"]) == 0, f"fresh game must have 0 guesses, got {len(data['guesses'])}"


def test_c_1_4_post_guess_echoes_code_and_turn(client: httpx.Client):
    game_id, _ = create_game(client)
    code = [0, 1, 2, 3]
    r = client.post(f"/api/games/{game_id}/guesses", json={"code": code})
    assert r.status_code == 201, f"expected 201 posting guess, got {r.status_code}: {r.text}"
    data = r.json()
    assert data.get("code") == code, f"response must echo code, got {data}"
    assert isinstance(data.get("turn"), int) and data["turn"] >= 1, f"turn must be a positive integer, got {data}"


def test_c_4_1_get_games_lists_entries_with_fields(client: httpx.Client):
    # Create two games and make one guess in the second game so guessCount differs
    g1, _ = create_game(client, seed=42)
    g2, _ = create_game(client, seed=7)
    post_guess(client, g2, [0, 0, 0, 0])

    r = client.get("/api/games")
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text}"
    items = r.json()
    assert isinstance(items, list), f"list endpoint must return an array, got {type(items)}"

    # Filter to the two we just created
    by_id = {it["id"]: it for it in items if it.get("id") in {g1, g2}}
    assert g1 in by_id and g2 in by_id, f"response should include created games, got keys: {list(by_id)}"

    for gid, it in by_id.items():
        assert isinstance(it.get("seed"), int), f"entry must include numeric seed: {it}"
        assert isinstance(it.get("guessCount"), int), f"entry must include numeric guessCount: {it}"
        assert it.get("status") in {"in_progress", "won"}, f"entry must include valid status: {it}"

    assert by_id[g1]["guessCount"] == 0, f"first game should have 0 guesses, got {by_id[g1]}"
    assert by_id[g2]["guessCount"] == 1, f"second game should have 1 guess, got {by_id[g2]}"
