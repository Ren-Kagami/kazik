"""
Probability calculations and analysis for the slot machine.
"""

import random
from typing import List, Dict, Tuple
from collections import Counter
import logging

from app.core.config import SYMBOLS, SYMBOL_WEIGHTS, PAYOUT_MULTIPLIERS

logger = logging.getLogger(__name__)


class ProbabilityCalculator:
    """Handle probability calculations for slot machine outcomes."""

    def __init__(self) -> None:
        """Initialize the probability calculator."""
        self.symbols = SYMBOLS
        self.weights = SYMBOL_WEIGHTS
        self.payouts = PAYOUT_MULTIPLIERS
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """Validate that symbols, weights, and payouts are properly configured."""
        if len(self.symbols) != len(self.weights):
            raise ValueError("Symbols and weights must have the same length")

        if not all(symbol in self.payouts for symbol in self.symbols):
            raise ValueError("All symbols must have corresponding payout multipliers")

        logger.info(f"Initialized with {len(self.symbols)} symbols")

    def spin_reels(self, num_reels: int = 3) -> List[str]:
        """
        Spin the slot machine reels and return the result.

        Args:
            num_reels: Number of reels to spin

        Returns:
            List of symbols, one for each reel
        """
        result = random.choices(self.symbols, weights=self.weights, k=num_reels)
        logger.info(f"Spin result: {result}")
        return result

    def calculate_payout(self, spin_result: List[str], bet_amount: int) -> int:
        """
        Calculate payout for a given spin result.

        Args:
            spin_result: List of symbols from the spin
            bet_amount: Amount bet on this spin

        Returns:
            Payout amount (0 if no win)
        """
        if not spin_result:
            return 0

        # Check for matching symbols
        symbol_counts = Counter(spin_result)
        max_count = max(symbol_counts.values())

        if max_count < 2:
            return 0

        # Find the most valuable matching symbol
        matching_symbols = [symbol for symbol, count in symbol_counts.items()
                          if count == max_count]
        best_symbol = max(matching_symbols, key=lambda s: self.payouts[s])

        # Calculate payout based on matches and symbol value
        multiplier = self.payouts[best_symbol]
        if max_count == 3:
            multiplier *= 2  # Bonus for three of a kind

        payout = bet_amount * multiplier
        logger.info(f"Payout calculated: {payout} (symbol: {best_symbol}, matches: {max_count})")
        return payout

    def get_symbol_probabilities(self) -> Dict[str, float]:
        """
        Calculate the probability of each symbol appearing.

        Returns:
            Dictionary mapping symbols to their probabilities
        """
        total_weight = sum(self.weights)
        return {
            symbol: weight / total_weight
            for symbol, weight in zip(self.symbols, self.weights)
        }
