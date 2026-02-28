# risk_manager.py — Session-scoped bet guard.
# Tracks budget spent and markets already bet in this session.
# Single Responsibility: approve or reject a bet before it reaches trader.py.

import logging

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Enforces per-session betting constraints:
      - Hard budget cap (MAX_BET_BUDGET_USD)
      - Fixed stake per bet (BET_STAKE_USD)
      - Duplicate guard: no two bets on the same token in one session

    One instance is created per game session by scheduler.py and passed to
    run_single_scan() on every scan iteration within that session.
    """

    def __init__(self, max_budget: float, stake_per_bet: float) -> None:
        self._max_budget = max_budget
        self._stake = stake_per_bet
        self._spent = 0.0
        self._placed: set[str] = set()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def approve(self, token_id: str) -> tuple[bool, str]:
        """
        Check whether a bet on token_id is permitted.
        Returns (True, "ok") or (False, reason_string).
        """
        if token_id in self._placed:
            return False, "duplicate"
        if self._spent + self._stake > self._max_budget:
            return False, "budget_exceeded"
        return True, "ok"

    def record_bet(self, token_id: str) -> None:
        """Call after a successful order to update session state."""
        self._placed.add(token_id)
        self._spent += self._stake
        logger.info(
            "Bet recorded. Session spent: $%.2f / $%.2f",
            self._spent, self._max_budget,
        )

    # ------------------------------------------------------------------
    # Read-only properties for logging / Telegram messages
    # ------------------------------------------------------------------

    @property
    def spent(self) -> float:
        return self._spent

    @property
    def remaining(self) -> float:
        return self._max_budget - self._spent

    @property
    def bets_placed(self) -> int:
        return len(self._placed)
