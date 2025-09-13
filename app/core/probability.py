"""
Probability calculation engine for slot machine game.
Handles symbol weights, payout calculations, and theoretical RTP.
"""

import random
import math
from typing import List, Dict, Tuple, Optional
from collections import Counter
import itertools

from app.core.config import (
    DEFAULT_SYMBOLS,
    DEFAULT_WEIGHTS,
    DEFAULT_PAYOUTS,
    NUM_REELS,
    logger
)


class ProbabilityCalculator:
    """
    Handles all probability calculations for the slot machine.

    This class manages symbol weights, calculates payouts,
    and provides theoretical Return to Player (RTP) calculations.
    """

    def __init__(
        self,
        symbols: List[str] = None,
        weights: List[int] = None,
        payouts: Dict[str, int] = None
    ):
        """
        Initialize the probability calculator.

        Args:
            symbols: List of slot machine symbols
            weights: List of weights corresponding to each symbol
            payouts: Dictionary mapping symbols to payout multipliers
        """
        self.symbols = symbols or DEFAULT_SYMBOLS.copy()
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self.payouts = payouts or DEFAULT_PAYOUTS.copy()
        self.num_reels = NUM_REELS

        # Validate configuration
        self._validate_configuration()

        # Calculate probabilities
        self._calculate_probabilities()

        logger.info(
            f"Probability calculator initialized with {len(self.symbols)} symbols, "
            f"{self.num_reels} reels"
        )

    def _validate_configuration(self):
        """
        Validate the probability configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        if len(self.symbols) != len(self.weights):
            raise ValueError("Symbols and weights must have same length")

        if not all(weight > 0 for weight in self.weights):
            raise ValueError("All weights must be positive")

        if not all(symbol in self.payouts for symbol in self.symbols):
            raise ValueError("All symbols must have payout multipliers")

        if not all(payout > 0 for payout in self.payouts.values()):
            raise ValueError("All payout multipliers must be positive")

    def _calculate_probabilities(self):
        """Calculate individual symbol probabilities."""
        total_weight = sum(self.weights)
        self.probabilities = [weight / total_weight for weight in self.weights]

    def spin_reels(self) -> List[str]:
        """
        Simulate a single spin of all reels.

        Returns:
            List of symbols, one for each reel
        """
        return random.choices(
            population=self.symbols,
            weights=self.weights,
            k=self.num_reels
        )

    def calculate_payout(self, symbols: List[str], bet_amount: int) -> int:
        """
        Calculate payout for given symbol combination.

        Args:
            symbols: List of symbols from the spin
            bet_amount: Amount bet on this spin

        Returns:
            Payout amount (0 if no win)
        """
        if len(symbols) != self.num_reels:
            raise ValueError(f"Expected {self.num_reels} symbols, got {len(symbols)}")

        # Count occurrences of each symbol
        symbol_counts = Counter(symbols)

        # Find the most frequent symbol and its count
        most_common_symbol, max_count = symbol_counts.most_common(1)[0]

        # Calculate payout based on matching symbols
        if max_count >= 2:  # At least 2 matching symbols
            base_multiplier = self.payouts.get(most_common_symbol, 0)

            # Bonus for more matches
            match_bonus = {2: 1.0, 3: 2.0, 4: 4.0, 5: 8.0}.get(max_count, 1.0)

            return int(bet_amount * base_multiplier * match_bonus)

        return 0

    def get_symbol_probabilities(self) -> Dict[str, float]:
        """
        Get individual symbol probabilities.

        Returns:
            Dictionary mapping symbols to their probabilities
        """
        return dict(zip(self.symbols, self.probabilities))

    def calculate_theoretical_rtp(self) -> float:
        """
        Calculate theoretical Return to Player percentage.

        Uses combinatorial analysis to compute exact RTP.

        Returns:
            Theoretical RTP as a percentage
        """
        total_payout = 0
        total_combinations = 0

        # Generate all possible combinations
        for combination in itertools.product(self.symbols, repeat=self.num_reels):
            # Calculate probability of this combination
            prob = 1.0
            for symbol in combination:
                symbol_index = self.symbols.index(symbol)
                prob *= self.probabilities[symbol_index]

            # Calculate payout for this combination (using bet_amount=1 for simplicity)
            payout = self.calculate_payout(list(combination), 1)

            # Add to expected value
            total_payout += payout * prob
            total_combinations += 1

        # RTP is expected payout per unit bet
        rtp = total_payout * 100

        logger.info(f"Theoretical RTP calculated: {rtp:.2f}%")
        return rtp

    def calculate_win_probability(self) -> float:
        """
        Calculate probability of any winning combination.

        Returns:
            Win probability as a percentage
        """
        win_combinations = 0
        total_combinations = 0

        for combination in itertools.product(self.symbols, repeat=self.num_reels):
            payout = self.calculate_payout(list(combination), 1)
            if payout > 0:
                win_combinations += 1
            total_combinations += 1

        win_probability = (win_combinations / total_combinations) * 100
        return win_probability

    def get_symbol_distribution_analysis(self) -> Dict[str, Dict[str, float]]:
        """
        Analyze symbol distribution and expected values.

        Returns:
            Dictionary with analysis data for each symbol
        """
        analysis = {}

        for i, symbol in enumerate(self.symbols):
            prob = self.probabilities[i]
            payout_multiplier = self.payouts[symbol]

            # Expected value contribution
            expected_contribution = prob * payout_multiplier

            analysis[symbol] = {
                "probability": prob,
                "weight": self.weights[i],
                "payout_multiplier": payout_multiplier,
                "expected_contribution": expected_contribution,
                "frequency_rank": sorted(
                    self.probabilities, reverse=True
                ).index(prob) + 1
            }

        return analysis

    def update_configuration(
        self,
        symbols: List[str],
        weights: List[int],
        payouts: Dict[str, int]
    ) -> bool:
        """
        Update probability configuration with new values.

        Args:
            symbols: New symbol list
            weights: New weight list
            payouts: New payout multipliers

        Returns:
            True if update successful, False otherwise
        """
        try:
            # Validate new configuration
            if len(symbols) != len(weights):
                raise ValueError("Symbols and weights must have same length")

            if not all(weight > 0 for weight in weights):
                raise ValueError("All weights must be positive")

            if not all(symbol in payouts for symbol in symbols):
                raise ValueError("All symbols must have payout multipliers")

            # Update configuration
            self.symbols = symbols.copy()
            self.weights = weights.copy()
            self.payouts = payouts.copy()

            # Recalculate probabilities
            self._calculate_probabilities()

            logger.info("Probability configuration updated successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False

    def simulate_spins(self, num_spins: int, bet_amount: int = 1) -> Dict[str, float]:
        """
        Run simulation to verify theoretical calculations.

        Args:
            num_spins: Number of spins to simulate
            bet_amount: Bet amount per spin

        Returns:
            Dictionary with simulation results
        """
        total_bet = num_spins * bet_amount
        total_payout = 0
        wins = 0

        for _ in range(num_spins):
            symbols = self.spin_reels()
            payout = self.calculate_payout(symbols, bet_amount)
            total_payout += payout

            if payout > 0:
                wins += 1

        actual_rtp = (total_payout / total_bet) * 100 if total_bet > 0 else 0
        win_rate = (wins / num_spins) * 100 if num_spins > 0 else 0

        return {
            "spins": num_spins,
            "total_bet": total_bet,
            "total_payout": total_payout,
            "actual_rtp": actual_rtp,
            "win_rate": win_rate,
            "theoretical_rtp": self.calculate_theoretical_rtp()
        }

    def get_configuration_summary(self) -> Dict[str, any]:
        """
        Get complete configuration summary for debugging/admin purposes.

        Returns:
            Dictionary with complete configuration data
        """
        return {
            "symbols": self.symbols,
            "weights": self.weights,
            "probabilities": self.get_symbol_probabilities(),
            "payouts": self.payouts,
            "num_reels": self.num_reels,
            "theoretical_rtp": self.calculate_theoretical_rtp(),
            "win_probability": self.calculate_win_probability(),
            "symbol_analysis": self.get_symbol_distribution_analysis()
        }