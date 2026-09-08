# encoding: utf-8
from typing import Iterator, List, Tuple


def xorshift32_stream(seed: int) -> Iterator[int]:
    x = seed & 0xFFFFFFFF
    while True:
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= (x >> 17) & 0xFFFFFFFF
        x ^= (x << 5) & 0xFFFFFFFF
        x &= 0xFFFFFFFF
        yield x


def derive_secret(seed: int) -> List[int]:
    stream = xorshift32_stream(seed)
    return [next(stream) % 6 for _ in range(4)]


def score_guess(secret: List[int], guess: List[int]) -> Tuple[int, int]:
    black = sum(1 for i in range(4) if secret[i] == guess[i])
    counts_secret = [0] * 6
    counts_guess = [0] * 6
    for v in secret:
        counts_secret[v] += 1
    for v in guess:
        counts_guess[v] += 1
    overlap = sum(min(counts_secret[c], counts_guess[c]) for c in range(6))
    white = overlap - black
    return black, white


def find_seed_with_distinct_secret(start: int = 42, limit: int = 10000):
    for s in range(start, start + limit):
        sec = derive_secret(s)
        if len(set(sec)) == 4:
            return s, sec
    return start, derive_secret(start)


def all_codes() -> List[List[int]]:
    out: List[List[int]] = []
    for a in range(6):
        for b in range(6):
            for c in range(6):
                for d in range(6):
                    out.append([a, b, c, d])
    return out
