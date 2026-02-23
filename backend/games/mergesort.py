"""
Interactive Merge Sort engine.

The state dict stored in MergeSortSession.state has this shape:
{
    "pending":   [[id, id, ...], ...],   # sublists still waiting to be merged
    "left":      [id, ...],              # left half of the current merge
    "right":     [id, ...],              # right half of the current merge
    "result":    [id, ...],              # elements already placed in this merge
    "done":      int,                    # comparisons answered so far
    "total":     int,                    # total comparisons needed (fixed at start)
    "finished":  bool,                   # True when sort is complete
    "final":     [id, ...] | null,       # final ordered list (best → worst)
}
"""

import math


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _total_comparisons(n: int) -> int:
    """Upper bound on comparisons for merge sort with n elements."""
    if n <= 1:
        return 0
    total = 0
    size = 1
    while size < n:
        for start in range(0, n, size * 2):
            mid = min(start + size, n)
            end = min(start + size * 2, n)
            left_len = mid - start
            right_len = end - mid
            total += left_len + right_len - 1
        size *= 2
    return total


def _assign_tiers(ordered_ids: list[int]) -> list[dict]:
    """
    Assign S/A/B/C/D tiers to an ordered list (index 0 = best).
    Distribution: S ~10%, A ~20%, B ~30%, C ~25%, D ~15%
    """
    n = len(ordered_ids)
    cutoffs = [
        ("S", math.ceil(n * 0.10)),
        ("A", math.ceil(n * 0.20)),
        ("B", math.ceil(n * 0.30)),
        ("C", math.ceil(n * 0.25)),
        ("D", n),  # everything else
    ]
    result = []
    placed = 0
    for tier, count in cutoffs:
        for game_id in ordered_ids[placed: placed + count]:
            result.append({"id": game_id, "tier": tier})
        placed += count
        if placed >= n:
            break
    return result


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def build_initial_state(game_ids: list[int]) -> dict:
    """
    Create the initial state for a new session.
    Starts by treating each element as its own sorted sublist, then
    kicks off the first merge so the first pair is ready immediately.
    """
    ids = list(game_ids)
    n = len(ids)
    # each element is already a trivially sorted sublist
    pending = [[gid] for gid in ids]
    state = {
        "pending": pending,
        "left": [],
        "right": [],
        "result": [],
        "done": 0,
        "total": _total_comparisons(n),
        "finished": False,
        "final": None,
    }
    return _advance(state)


def current_pair(state: dict) -> tuple[int, int] | None:
    """Return the two game ids the user must compare right now, or None if done."""
    if state["finished"]:
        return None
    if not state["left"] and not state["right"]:
        return None
    return (state["left"][0], state["right"][0])


def answer(state: dict, winner_id: int, loser_id: int) -> dict:
    """
    Record a comparison result and advance the algorithm.
    winner_id beat loser_id in the user's opinion.
    Returns the updated state.
    """
    if state["finished"]:
        return state

    left = state["left"]
    right = state["right"]

    if not left or not right:
        raise ValueError("No active comparison to answer")

    if winner_id == left[0] and loser_id == right[0]:
        # left wins: take left[0] into result, keep right intact
        state["result"].append(left.pop(0))
    elif winner_id == right[0] and loser_id == left[0]:
        # right wins: take right[0] into result, keep left intact
        state["result"].append(right.pop(0))
    else:
        raise ValueError(f"winner/loser don't match the current pair ({left[0]}, {right[0]})")

    state["done"] += 1
    return _advance(state)


# ---------------------------------------------------------------------------
# internal
# ---------------------------------------------------------------------------

def _advance(state: dict) -> dict:
    """
    Drive the algorithm forward until we either need a user comparison
    or the sort is fully complete.
    """
    while True:
        left = state["left"]
        right = state["right"]

        # --- still in the middle of a merge ---
        if left and right:
            # need user input for (left[0], right[0])
            break

        # --- one side of the current merge is exhausted ---
        if left or right:
            # flush the remaining side: no comparisons needed
            state["result"].extend(left or right)
            state["left"] = []
            state["right"] = []
            # push merged result onto pending
            state["pending"].append(state["result"])
            state["result"] = []

        # --- start the next merge if possible ---
        if len(state["pending"]) >= 2:
            state["left"] = state["pending"].pop(0)
            state["right"] = state["pending"].pop(0)
            state["result"] = []
            # if both sides have exactly one element each, we need user input
            if state["left"] and state["right"]:
                continue  # loop back — if one side is already empty, flush it
        elif len(state["pending"]) == 1:
            # only one sublist left → that's the final sorted order
            state["final"] = state["pending"][0]
            state["finished"] = True
            state["pending"] = []
            break
        else:
            # nothing pending and no active merge — shouldn't normally happen
            state["finished"] = True
            break

    return state