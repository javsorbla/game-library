"""
Two-phase tournament engine — merge sort in both phases.

Phase 1 (groups): games split by first genre, sorted via merge sort within
                  each group. Top 3 by final position advance.
Phase 2 (final):  finalists sorted via merge sort.

Tiers for finalists by position: S(top 1), A(next 20%), B(next 30%), C(rest).
Eliminated games -> tier D, ordered by position within their group.

Merge sort state (reused for both group and final):
{
  "pending": [[id,...], ...],   # sublists yet to be merged
  "left":    [id, ...],         # left half of current merge
  "right":   [id, ...],         # right half of current merge
  "result":  [id, ...],         # elements placed so far in this merge
  "ms_done": int,
  "ms_total": int,
}
"""

import math


FINALISTS_PER_GROUP = 3
TIER_LAYOUT = [("S", 1), ("A", 0.20), ("B", 0.30)]  # rest -> C


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def build_initial_state(games_with_genre: list[tuple[int, str]]) -> dict:
    genre_map: dict[str, list[int]] = {}
    for gid, genre in games_with_genre:
        key = genre.strip() or "Uncategorised"
        genre_map.setdefault(key, []).append(gid)

    groups = []
    total_comparisons = 0
    for genre, ids in genre_map.items():
        ms = _ms_build(ids)
        total_comparisons += ms["ms_total"]
        groups.append({"genre": genre, "games": ids, "ms": ms, "sorted": None})

    return _advance({
        "phase":   "groups",
        "groups":  groups,
        "final":   None,
        "done":    0,
        "total":   total_comparisons,
        "ranking": None,
    })


def current_pair(state: dict) -> tuple[int, int] | None:
    if state["phase"] == "groups":
        grp = _active_group(state)
        if grp:
            return _ms_current_pair(grp["ms"])
    elif state["phase"] == "final":
        return _ms_current_pair(state["final"]["ms"])
    return None


def answer(state: dict, winner_id: int, loser_id: int) -> dict:
    if state["phase"] == "groups":
        grp = _active_group(state)
        if not grp:
            raise ValueError("No active group comparison.")
        _ms_answer(grp["ms"], winner_id, loser_id)

    elif state["phase"] == "final":
        _ms_answer(state["final"]["ms"], winner_id, loser_id)

    else:
        raise ValueError("Tournament is already finished.")

    state["done"] += 1
    return _advance(state)


def current_group_info(state: dict) -> dict | None:
    if state["phase"] != "groups":
        return None
    grp = _active_group(state)
    if not grp:
        return None
    ms = grp["ms"]
    return {"genre": grp["genre"], "done": ms["ms_done"], "total": ms["ms_total"]}


def all_game_ids(state: dict) -> list[int]:
    ids = set()
    for grp in state.get("groups", []):
        ids.update(grp["games"])
    if state.get("final"):
        ids.update(state["final"]["games"])
    return list(ids)


# ---------------------------------------------------------------------------
# internal — state machine
# ---------------------------------------------------------------------------

def _active_group(state: dict) -> dict | None:
    for grp in state["groups"]:
        if grp["sorted"] is None:
            return grp
    return None


def _advance(state: dict) -> dict:
    if state["phase"] == "groups":
        # keep advancing until we need user input or all groups are sorted
        while True:
            grp = _active_group(state)
            if not grp:
                break
            _ms_advance(grp["ms"])
            if _ms_finished(grp["ms"]):
                grp["sorted"] = grp["ms"]["pending"][0]
                # loop to check next group
                continue
            break  # this group needs user input

        if not _active_group(state):
            _start_final(state)

    if state["phase"] == "final":
        _ms_advance(state["final"]["ms"])
        if _ms_finished(state["final"]["ms"]):
            _finish(state)

    return state


def _start_final(state: dict) -> None:
    finalists, eliminated = [], []
    for grp in state["groups"]:
        sorted_ids = grp["sorted"]
        top = sorted_ids[:FINALISTS_PER_GROUP]
        rest = sorted_ids[FINALISTS_PER_GROUP:]
        finalists.extend(top)
        for rank, gid in enumerate(rest):
            eliminated.append({"id": gid, "group_rank": FINALISTS_PER_GROUP + rank})

    ms = _ms_build(finalists)
    state["total"] += ms["ms_total"]
    state["final"] = {"games": finalists, "eliminated": eliminated, "ms": ms}
    state["phase"] = "final"


def _assign_tiers(n: int) -> list[str]:
    tiers, pos = [], 0
    for tier, amount in TIER_LAYOUT:
        count = 1 if isinstance(amount, int) else max(1, math.ceil(n * amount))
        for _ in range(min(count, n - pos)):
            tiers.append(tier)
            pos += 1
    while pos < n:
        tiers.append("C")
        pos += 1
    return tiers


def _finish(state: dict) -> None:
    fin        = state["final"]
    sorted_ids = fin["ms"]["pending"][0]
    tier_labels = _assign_tiers(len(sorted_ids))

    ranking = [
        {"id": gid, "tier": tier_labels[i], "rank": i + 1, "wins": None}
        for i, gid in enumerate(sorted_ids)
    ]
    eliminated = sorted(fin["eliminated"], key=lambda x: x["group_rank"])
    for j, entry in enumerate(eliminated, start=len(ranking) + 1):
        ranking.append({"id": entry["id"], "tier": "D", "rank": j, "wins": None})

    state["ranking"] = ranking
    state["phase"]   = "finished"


# ---------------------------------------------------------------------------
# internal — merge sort primitives (reused for groups and final)
# ---------------------------------------------------------------------------

def _ms_total_comparisons(n: int) -> int:
    if n <= 1:
        return 0
    total, size = 0, 1
    while size < n:
        for start in range(0, n, size * 2):
            left_len  = min(size, n - start)
            right_len = min(size, n - start - left_len)
            if right_len > 0:
                total += left_len + right_len - 1
        size *= 2
    return total


def _ms_build(ids: list[int]) -> dict:
    """Create a fresh merge sort state for a list of ids."""
    return {
        "pending":  [[gid] for gid in ids],
        "left":     [],
        "right":    [],
        "result":   [],
        "ms_done":  0,
        "ms_total": _ms_total_comparisons(len(ids)),
    }


def _ms_current_pair(ms: dict) -> tuple[int, int] | None:
    if ms["left"] and ms["right"]:
        return (ms["left"][0], ms["right"][0])
    return None


def _ms_finished(ms: dict) -> bool:
    return (
        not ms["left"]
        and not ms["right"]
        and not ms["result"]
        and len(ms["pending"]) == 1
    )


def _ms_answer(ms: dict, winner_id: int, loser_id: int) -> None:
    left, right = ms["left"], ms["right"]
    if not left or not right:
        raise ValueError("No active merge sort comparison.")
    if set([left[0], right[0]]) != {winner_id, loser_id}:
        raise ValueError(f"Expected {left[0]} vs {right[0]}, got {winner_id} vs {loser_id}.")
    if winner_id == left[0]:
        ms["result"].append(left.pop(0))
    else:
        ms["result"].append(right.pop(0))
    ms["ms_done"] += 1


def _ms_advance(ms: dict) -> None:
    """Drive merge sort forward until user input is needed or sort is done."""
    while True:
        if ms["left"] and ms["right"]:
            break  # need user input

        # flush exhausted side
        if ms["left"] or ms["right"]:
            ms["result"].extend(ms["left"] or ms["right"])
            ms["left"], ms["right"] = [], []
            ms["pending"].append(ms["result"])
            ms["result"] = []

        if len(ms["pending"]) >= 2:
            ms["left"]  = ms["pending"].pop(0)
            ms["right"] = ms["pending"].pop(0)
            ms["result"] = []
            continue

        break