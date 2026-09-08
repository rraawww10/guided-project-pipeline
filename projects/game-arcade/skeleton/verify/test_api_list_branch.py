# encoding: utf-8
from typing import List


def test_c_4_1_games_list_returns_summaries_with_guess_counts(http_client):
    # Create two games, add differing numbers of guesses
    g1 = http_client.post("/api/games", json={"seed": 1001}).json()
    g2 = http_client.post("/api/games", json={"seed": 1002}).json()
    # Add two guesses to g1, one to g2
    http_client.post(f"/api/games/{g1['id']}/guesses", json={"code": [0, 0, 0, 0]})
    http_client.post(f"/api/games/{g1['id']}/guesses", json={"code": [1, 1, 1, 1]})
    http_client.post(f"/api/games/{g2['id']}/guesses", json={"code": [2, 2, 2, 2]})

    res = http_client.get("/api/games")
    assert res.status_code == 200
    arr = res.json()
    # Find our two games and check their guessCount fields
    by_id = {row.get("id"): row for row in arr}
    assert g1["id"] in by_id and g2["id"] in by_id
    assert by_id[g1["id"]].get("seed") == 1001
    assert by_id[g2["id"]].get("seed") == 1002
    assert by_id[g1["id"]].get("guessCount") == 2
    assert by_id[g2["id"]].get("guessCount") == 1


def test_c_4_4_branch_endpoint_creates_new_game_with_k_copied_guesses(http_client):
    # Create a source game with 3 guesses
    src = http_client.post("/api/games", json={"seed": 2024}).json()
    g_codes = [[0, 1, 2, 3], [3, 2, 1, 0], [5, 4, 3, 2]]
    for code in g_codes:
        http_client.post(f"/api/games/{src['id']}/guesses", json={"code": code})

    # Branch upto k=2
    br = http_client.post(f"/api/games/{src['id']}/branch", json={"upto": 2})
    assert br.status_code == 201
    branched = br.json()

    # GET the branched game and verify exactly first k guesses copied (code and scores)
    got = http_client.get(f"/api/games/{branched['id']}")
    assert got.status_code == 200
    body = got.json()
    guesses = body.get("guesses")
    assert isinstance(guesses, list) and len(guesses) == 2
    for i, g in enumerate(guesses):
        assert g.get("code") == g_codes[i]
        # Scores must also be copied (numeric)
        assert isinstance(g.get("black"), int)
        assert isinstance(g.get("white"), int)
