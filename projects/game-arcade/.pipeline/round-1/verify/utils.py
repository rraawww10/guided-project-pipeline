# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional, Tuple
import time
import httpx


def secret_from_seed(seed: int) -> List[int]:
    """Compute the 4-long base-6 code from the seed as per spec.

    secret[i] = floor(seed / 6^i) % 6 for i in 0..3
    Least-significant digit first.
    """
    out = []
    for i in range(4):
        out.append((seed // (6 ** i)) % 6)
    return out


def rotate_right(code: List[int]) -> List[int]:
    if not code:
        return code
    return [code[-1]] + code[:-1]


def create_game(client: httpx.Client, seed: Optional[int] = None) -> Tuple[str, int]:
    payload = ({"seed": seed} if seed is not None else {})
    r = client.post("/api/games", json=payload)
    assert r.status_code == 201, f"Expected 201 creating game, got {r.status_code}: {r.text}"
    data = r.json()
    assert isinstance(data.get("id"), str), f"id must be string, got: {data}"
    assert isinstance(data.get("seed"), int), f"seed must be number, got: {data}"
    return data["id"], data["seed"]


def post_guess(client: httpx.Client, game_id: str, code: List[int]) -> dict:
    r = client.post(f"/api/games/{game_id}/guesses", json={"code": code})
    assert r.status_code == 201, f"Expected 201 posting guess, got {r.status_code}: {r.text}"
    data = r.json()
    assert data.get("code") == code, f"echoed code must equal body, got {data}"
    assert isinstance(data.get("turn"), int), f"turn must be a number, got {data}"
    return data


def get_game(client: httpx.Client, game_id: str) -> dict:
    r = client.get(f"/api/games/{game_id}")
    assert r.status_code == 200, f"Expected 200 game detail, got {r.status_code}: {r.text}"
    return r.json()


def poll_guesses_len(client: httpx.Client, game_id: str, expected: int, timeout_s: float = 3.0) -> dict:
    """Poll the game until guesses length equals expected or timeout.
    Returns the game json.
    """
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        last = get_game(client, game_id)
        guesses = last.get("guesses") or []
        if len(guesses) == expected:
            return last
        time.sleep(0.1)
    assert False, f"Expected {expected} guesses, got {len((last or {}).get('guesses') or [])}: {last}"


def get_hint(client: httpx.Client, game_id: str) -> dict:
    r = client.get(f"/api/games/{game_id}/hint")
    assert r.status_code == 200, f"Expected 200 hint, got {r.status_code}: {r.text}"
    return r.json()
