# display.py — Terminal output formatting. No filtering or business logic here.

import logging
from tabulate import tabulate

logger = logging.getLogger(__name__)

_HEADERS = ["Match", "Min", "Score", "Leader", "Poly%", "Betfair%", "Edge"]


def print_results(opportunities: list[dict]) -> None:
    """Prints a clean, formatted table of opportunities to the terminal."""
    if not opportunities:
        print("\n[INFO] No statistically resolved matches detected.")
        return

    print("\n" + "="*80)
    print(f"{'STATISTICALLY RESOLVED MATCHES':^80}")
    print("="*80)
    
    header = f"{'MATCH':<30} | {'MIN':<3} | {'SCORE':<5} | {'RESOLVED':<15} | {'BOOKIE%'}"
    print(header)
    print("-" * len(header))

    for opp in opportunities:
        ref_p = f"{opp['reference_prob']*100:>6.1f}%"
        
        print(f"{opp['match'][:30]:<30} | {opp['minute']:<3} | {opp['score']:<5} | {opp['resolved_outcome'][:15]:<15} | {ref_p}")

    print("="*80 + "\n")


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
