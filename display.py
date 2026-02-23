# display.py — Terminal output formatting. No filtering or business logic here.

import logging
from tabulate import tabulate

logger = logging.getLogger(__name__)

_HEADERS = ["Match", "Min", "Score", "Leader", "Poly%", "Betfair%", "Edge"]


def print_results(opportunities: list[dict]) -> None:
    """Print a formatted table of opportunities. Clear message if none found."""
    if not opportunities:
        print("\n  ⚽  No qualifying matches right now. Try again during 75-90 min.\n")
        return

    rows = [_format_row(op) for op in opportunities]
    # match the look and feel requested - simple table
    print("\n" + tabulate(rows, headers=_HEADERS, tablefmt="plain"))
    print(f"\n  {len(opportunities)} opportunity(ies) found.\n")


def _format_row(op: dict) -> list:
    """Format one opportunity into a display row."""
    poly_pct = f"{int(op['poly_prob'] * 100)}%"
    ref_prob = op.get("reference_prob")
    betfair_pct = f"{int(ref_prob * 100)}%" if ref_prob is not None else "—"
    edge_str = _format_edge(op.get("edge"))

    return [
        op["match"],
        f"{op['minute']}'",
        op["score"],
        op["leader"],
        poly_pct,
        betfair_pct,
        edge_str,
    ]


def _format_edge(edge: float | None) -> str:
    """Format edge with a visual flag if meaningfully positive."""
    if edge is None:
        return "—"
    sign = "+" if edge >= 0 else ""
    flag = "  ← BET" if edge >= 0.05 else ""
    return f"{sign}{int(edge * 100)}%{flag}"
