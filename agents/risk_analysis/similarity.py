"""Deterministic ordinary Levenshtein similarity utilities."""


def levenshtein_distance(first: str, second: str) -> int:
    """Return ordinary Levenshtein edit distance (not Damerau-Levenshtein)."""
    if first == second:
        return 0
    if len(first) < len(second):
        first, second = second, first
    previous = list(range(len(second) + 1))
    for first_index, first_character in enumerate(first, start=1):
        current = [first_index]
        for second_index, second_character in enumerate(second, start=1):
            substitution_cost = 0 if first_character == second_character else 1
            current.append(min(
                current[-1] + 1,
                previous[second_index] + 1,
                previous[second_index - 1] + substitution_cost,
            ))
        previous = current
    return previous[-1]


def normalized_levenshtein_similarity(first: str, second: str) -> float:
    """Return 1 - distance / longest length, comparing names case-insensitively."""
    first = first.casefold()
    second = second.casefold()
    longest_length = max(len(first), len(second))
    if longest_length == 0:
        return 1.0
    return 1.0 - levenshtein_distance(first, second) / longest_length
