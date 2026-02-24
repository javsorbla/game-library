"""
Two-phase tournament engine — simplified.

Phase 1 (groups): games split by first genre, round robin within each group,
                  top 3 advance (all if group ≤ 3).
Phase 2 (final):  all finalists play round robin, ranked by wins.

Tiers assigned to finalists by position: S(top1), A(next 20%), B(next 30%), C(rest).
Eliminated games → tier D, ordered by win-percentage within their group.

State shape:
{
  "phase":   "groups" | "final" | "finished",
  "groups": [
    {
      "genre":   str,
      "games":   [id, ...],
      "wins":    {str(id): int},
      "pending": [[id, id], ...]
    }
  ],
  "final": {
    "games":   [id, ...],
    "wins":    {str(id): int},
    "pending": [[id, id], ...]
  } | null,
  "done":    int,
  "total":   int,
  "ranking": null | [{"id": int, "tier": str, "rank": int, "wins": int|null}]
}
"""

import math
from itertools import combinations


FINALISTS_PER_GROUP = 3
TIER_LAYOUT = [("S", 1), ("A", 0.20), ("B", 0.30)]  # rest → C


def build_initial_state(games_with_genre: list[tuple[int, str]]) -> dict:
    """games_with_genre: list of (game_id, genre_name) tuples."""
    genre_map: dict[str, list[int]] = {}
    for gid, genre in games_with_genre:
        key = genre.strip() or "Uncategorised"
        genre_map.setdefault(key, []).append(gid)

    groups = []
    total_comparisons = 0
    for genre, ids in genre_map.items():
        pending = _pairs(ids)
        total_comparisons += len(pending)
        groups.append({
            "genre":   genre,
            "games":   ids,
            "wins":    {str(i): 0 for i in ids},
            "pending": pending,
        })

    return _advance({
        "phase":   "groups",
        "groups":  groups,
        "final":   None,
        "done":    0,
        "total":   total_comparisons,
        "ranking": None,
    })


def current_pair(state: dict) -> tuple[int, int] | None:
    """Return the next pair to compare, or None if finished."""
    if state["phase"] == "groups":
        grp = _active_group(state)
        if grp:
            return tuple(grp["pending"][0])
    elif state["phase"] == "final":
        if state["final"]["pending"]:
            return tuple(state["final"]["pending"][0])
    return None


def answer(state: dict, winner_id: int, loser_id: int) -> dict:
    """Record a comparison and return the updated state."""
    if state["phase"] == "groups":
        grp = _active_group(state)
        if not grp:
            raise ValueError("No active group comparison.")
        _check_pair(grp["pending"][0], winner_id, loser_id)
        grp["wins"][str(winner_id)] += 1
        grp["pending"].pop(0)

    elif state["phase"] == "final":
        fin = state["final"]
        if not fin["pending"]:
            raise ValueError("No active final comparison.")
        _check_pair(fin["pending"][0], winner_id, loser_id)
        fin["wins"][str(winner_id)] += 1
        fin["pending"].pop(0)

    else:
        raise ValueError("Tournament is already finished.")

    state["done"] += 1
    return _advance(state)


def current_group_info(state: dict) -> dict | None:
    """Return {genre, done, total} for the active group, or None."""
    if state["phase"] != "groups":
        return None
    grp = _active_group(state)
    if not grp:
        return None
    total = len(_pairs(grp["games"]))
    done  = total - len(grp["pending"])
    return {"genre": grp["genre"], "done": done, "total": total}


def all_game_ids(state: dict) -> list[int]:
    """Return every game id referenced in the state."""
    ids = set()
    for grp in state.get("groups", []):
        ids.update(grp["games"])
    if state.get("final"):
        ids.update(state["final"]["games"])
    return list(ids)


# ---------------------------------------------------------------------------
# internal
# ---------------------------------------------------------------------------

def _pairs(ids: list[int]) -> list[list[int]]:
    return [list(p) for p in combinations(ids, 2)]


def _active_group(state: dict) -> dict | None:
    """Return the first group that still has pending comparisons."""
    for grp in state["groups"]:
        if grp["pending"]:
            return grp
    return None


def _check_pair(pair: list, winner_id: int, loser_id: int) -> None:
    if set(pair) != {winner_id, loser_id}:
        raise ValueError(f"Expected pair {pair}, got {winner_id} vs {loser_id}.")


def _advance(state: dict) -> dict:
    """Move the state machine forward whenever a phase is complete."""
    if state["phase"] == "groups" and not _active_group(state):
        _start_final(state)

    if state["phase"] == "final" and not state["final"]["pending"]:
        _finish(state)

    return state


def _top_from_group(grp: dict) -> tuple[list[int], list[dict]]:
    """Return (finalists, eliminated) for a completed group."""
    ids = grp["games"]
    n   = len(ids)
    max_wins = n - 1

    sorted_ids = sorted(ids, key=lambda i: grp["wins"][str(i)], reverse=True)
    cutoff = min(FINALISTS_PER_GROUP, n)

    # extend cutoff to include tied games at the boundary
    if cutoff < n:
        boundary = grp["wins"][str(sorted_ids[cutoff - 1])]
        while cutoff < n and grp["wins"][str(sorted_ids[cutoff])] == boundary:
            cutoff += 1

    finalists = sorted_ids[:cutoff]
    eliminated = [
        {"id": gid, "win_pct": grp["wins"][str(gid)] / max_wins if max_wins else 0.0}
        for gid in sorted_ids[cutoff:]
    ]
    return finalists, eliminated


def _start_final(state: dict) -> None:
    finalists, eliminated = [], []
    for grp in state["groups"]:
        f, e = _top_from_group(grp)
        finalists.extend(f)
        eliminated.extend(e)

    pending = _pairs(finalists)
    state["total"] += len(pending)
    state["final"] = {
        "games":      finalists,
        "wins":       {str(i): 0 for i in finalists},
        "pending":    pending,
        "eliminated": eliminated,
    }
    state["phase"] = "final"


def _assign_tiers(n: int) -> list[str]:
    """Return a tier label for each position 0..n-1."""
    tiers = []
    pos = 0
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
    fin = state["final"]
    sorted_ids = sorted(fin["games"], key=lambda i: fin["wins"][str(i)], reverse=True)
    tier_labels = _assign_tiers(len(sorted_ids))

    ranking = [
        {"id": gid, "tier": tier_labels[i], "rank": i + 1, "wins": fin["wins"][str(gid)]}
        for i, gid in enumerate(sorted_ids)
    ]

    # append eliminated as tier D, ordered by win_pct desc
    eliminated = sorted(fin["eliminated"], key=lambda x: x["win_pct"], reverse=True)
    for j, entry in enumerate(eliminated, start=len(ranking) + 1):
        ranking.append({"id": entry["id"], "tier": "D", "rank": j, "wins": None})

    state["ranking"] = ranking
    state["phase"]   = "finished"