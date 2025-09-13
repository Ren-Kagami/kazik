"""
FastAPI routes for slot machine game API.
"""

from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging
import asyncio
from datetime import datetime, timedelta

from app.models.slot_machine import (
    SessionCreate,
    SessionResponse,
    SpinRequest,
    SpinResponse,
    SimulationRequest,
    SimulationResponse,
    SessionStats,
    AdminProbabilityUpdate
)
from app.core.probability import ProbabilityCalculator
from app.core.config import INITIAL_CREDITS, logger
from app.core.session_manager import SessionManager
from app.core.admin import AdminManager

# Initialize components
router = APIRouter()
session_manager = SessionManager()
probability_calculator = ProbabilityCalculator()
admin_manager = AdminManager()


# Dependency for admin authentication
async def verify_admin_token(token: str = None):
    """Verify admin authentication token."""
    if not token or not admin_manager.verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return True


@router.post("/session", response_model=SessionResponse)
async def create_session() -> SessionResponse:
    """
    Create a new game session.

    Returns:
        SessionResponse: New session data with unique ID and initial credits
    """
    try:
        session = await session_manager.create_session(INITIAL_CREDITS)
        logger.info(f"Created new session: {session.session_id}")

        return SessionResponse(
            session_id=session.session_id,
            credits=session.credits,
            created_at=session.created_at,
            total_spins=session.total_spins,
            total_winnings=session.total_winnings
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    """
    Retrieve session data by ID.

    Args:
        session_id: Unique session identifier

    Returns:
        SessionResponse: Current session state
    """
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionResponse(
            session_id=session.session_id,
            credits=session.credits,
            created_at=session.created_at,
            total_spins=session.total_spins,
            total_winnings=session.total_winnings
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session")


@router.post("/spin/{session_id}", response_model=SpinResponse)
async def spin_slot_machine(session_id: str, request: SpinRequest) -> SpinResponse:
    """
    Perform a slot machine spin for given session.

    Args:
        session_id: Session identifier
        request: Spin request with bet amount

    Returns:
        SpinResponse: Spin result with symbols, payout, and updated session data
    """
    try:
        # Validate session
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Validate bet amount
        if request.bet_amount <= 0:
            raise HTTPException(status_code=400, detail="Bet amount must be positive")

        if request.bet_amount > session.credits:
            raise HTTPException(status_code=400, detail="Insufficient credits")

        # Perform spin using current probability settings
        symbols = probability_calculator.spin_reels()
        payout = probability_calculator.calculate_payout(symbols, request.bet_amount)

        # Update session
        new_credits = session.credits - request.bet_amount + payout
        updated_session = await session_manager.update_session(
            session_id,
            new_credits,
            session.total_spins + 1,
            session.total_winnings + payout
        )

        logger.info(f"Spin completed for session {session_id}: {symbols}, payout: {payout}")

        return SpinResponse(
            symbols=symbols,
            payout=payout,
            credits_remaining=new_credits,
            is_winner=payout > 0,
            session_data={
                "total_spins": updated_session.total_spins,
                "total_winnings": updated_session.total_winnings,
                "rtp": (updated_session.total_winnings / (updated_session.total_spins * request.bet_amount)) * 100
                if updated_session.total_spins > 0 else 0.0
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing spin for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process spin")


@router.get("/probability")
async def get_probability_data() -> Dict[str, Any]:
    """
    Get current probability configuration and theoretical RTP.

    Returns:
        Dict containing symbol probabilities and theoretical RTP
    """
    try:
        probabilities = probability_calculator.get_symbol_probabilities()
        theoretical_rtp = probability_calculator.calculate_theoretical_rtp()

        return {
            "symbol_probabilities": probabilities,
            "theoretical_rtp": theoretical_rtp,
            "payout_multipliers": probability_calculator.payouts,
            "symbols": probability_calculator.symbols,
            "weights": dict(zip(probability_calculator.symbols, probability_calculator.weights))
        }
    except Exception as e:
        logger.error(f"Error getting probability data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get probability data")


@router.post("/simulate", response_model=SimulationResponse)
async def run_simulation(request: SimulationRequest) -> SimulationResponse:
    """
    Run Monte Carlo simulation of slot machine spins.

    Args:
        request: Simulation parameters (number of spins, bet amount)

    Returns:
        SimulationResponse: Detailed simulation results and statistics
    """
    try:
        if request.num_simulations <= 0 or request.num_simulations > 100000:
            raise HTTPException(
                status_code=400,
                detail="Number of simulations must be between 1 and 100,000"
            )

        if request.bet_amount <= 0:
            raise HTTPException(status_code=400, detail="Bet amount must be positive")

        logger.info(f"Starting simulation: {request.num_simulations} spins")

        # Run simulation
        results = await run_monte_carlo_simulation(
            request.num_simulations,
            request.bet_amount
        )

        theoretical_rtp = probability_calculator.calculate_theoretical_rtp()

        return SimulationResponse(
            simulation_stats=results,
            comparison_data={
                "theoretical_rtp": theoretical_rtp,
                "actual_rtp": results["actual_rtp"],
                "rtp_difference": abs(theoretical_rtp - results["actual_rtp"]),
                "sample_size_sufficient": request.num_simulations >= 10000
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running simulation: {e}")
        raise HTTPException(status_code=500, detail="Simulation failed")


async def run_monte_carlo_simulation(num_simulations: int, bet_amount: int) -> Dict[str, Any]:
    """
    Execute Monte Carlo simulation with given parameters.

    Args:
        num_simulations: Number of spins to simulate
        bet_amount: Bet amount per spin

    Returns:
        Dict with simulation statistics
    """
    total_bet = num_simulations * bet_amount
    total_payout = 0
    wins = 0
    biggest_win = 0
    win_distribution = {}

    # Process in batches to avoid blocking
    batch_size = 1000
    for i in range(0, num_simulations, batch_size):
        current_batch = min(batch_size, num_simulations - i)

        for _ in range(current_batch):
            symbols = probability_calculator.spin_reels()
            payout = probability_calculator.calculate_payout(symbols, bet_amount)
            total_payout += payout

            if payout > 0:
                wins += 1
                if payout > biggest_win:
                    biggest_win = payout

                # Track win distribution
                payout_tier = payout // bet_amount  # Multiplier tier
                win_distribution[payout_tier] = win_distribution.get(payout_tier, 0) + 1

        # Yield control to prevent blocking
        if i % 5000 == 0:
            await asyncio.sleep(0.001)

    return {
        "total_spins": num_simulations,
        "total_bet": total_bet,
        "total_payout": total_payout,
        "net_result": total_payout - total_bet,
        "win_rate": (wins / num_simulations) * 100,
        "actual_rtp": (total_payout / total_bet) * 100,
        "biggest_win": biggest_win,
        "average_win": total_payout / wins if wins > 0 else 0,
        "win_distribution": win_distribution
    }


@router.get("/sessions/stats", response_model=List[SessionStats])
async def get_session_statistics(
        hours: int = 24,
        limit: int = 100
) -> List[SessionStats]:
    """
    Get session statistics for the specified time period.

    Args:
        hours: Look back period in hours (default: 24)
        limit: Maximum number of sessions to return (default: 100)

    Returns:
        List of session statistics
    """
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        sessions = await session_manager.get_recent_sessions(since, limit)

        stats = []
        for session in sessions:
            rtp = 0.0
            if session.total_spins > 0:
                # Assuming average bet of 10 for RTP calculation
                total_bet_estimate = session.total_spins * 10
                rtp = (session.total_winnings / total_bet_estimate) * 100

            stats.append(SessionStats(
                session_id=session.session_id,
                created_at=session.created_at,
                total_spins=session.total_spins,
                total_winnings=session.total_winnings,
                final_credits=session.credits,
                estimated_rtp=rtp
            ))

        return stats

    except Exception as e:
        logger.error(f"Error getting session statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session statistics")


# Admin endpoints
@router.post("/admin/probability/update")
async def update_probability_settings(
        request: AdminProbabilityUpdate,
        admin_verified: bool = Depends(verify_admin_token)
) -> Dict[str, Any]:
    """
    Update probability settings (Admin only).

    Args:
        request: New probability configuration
        admin_verified: Admin verification dependency

    Returns:
        Updated probability configuration
    """
    try:
        # Validate weights sum to reasonable total
        if not (50 <= sum(request.symbol_weights.values()) <= 200):
            raise HTTPException(
                status_code=400,
                detail="Symbol weights sum must be between 50 and 200"
            )

        # Update probability calculator
        success = probability_calculator.update_configuration(
            list(request.symbol_weights.keys()),
            list(request.symbol_weights.values()),
            request.payout_multipliers
        )

        if not success:
            raise HTTPException(status_code=400, detail="Invalid probability configuration")

        # Log admin action
        logger.info(f"Admin updated probability settings: {request}")

        return {
            "message": "Probability settings updated successfully",
            "new_configuration": await get_probability_data(),
            "updated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating probability settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update probability settings")


@router.get("/admin/sessions/analytics")
async def get_admin_analytics(
        admin_verified: bool = Depends(verify_admin_token)
) -> Dict[str, Any]:
    """
    Get comprehensive analytics for admin panel.

    Args:
        admin_verified: Admin verification dependency

    Returns:
        Detailed analytics data
    """
    try:
        # Get recent session data
        recent_sessions = await session_manager.get_recent_sessions(
            datetime.utcnow() - timedelta(hours=24),
            1000
        )

        # Calculate analytics
        total_sessions = len(recent_sessions)
        total_spins = sum(s.total_spins for s in recent_sessions)
        total_winnings = sum(s.total_winnings for s in recent_sessions)
        active_sessions = len([s for s in recent_sessions if s.credits > 0])

        # Estimate total bets (assuming average bet of 10)
        estimated_total_bets = total_spins * 10
        house_edge = ((
                                  estimated_total_bets - total_winnings) / estimated_total_bets * 100) if estimated_total_bets > 0 else 0

        return {
            "period_hours": 24,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_spins": total_spins,
            "total_winnings": total_winnings,
            "estimated_total_bets": estimated_total_bets,
            "house_edge_percent": house_edge,
            "average_spins_per_session": total_spins / total_sessions if total_sessions > 0 else 0,
            "current_probability_config": await get_probability_data(),
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting admin analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics data")


@router.delete("/admin/sessions/{session_id}")
async def delete_session(
        session_id: str,
        admin_verified: bool = Depends(verify_admin_token)
) -> Dict[str, str]:
    """
    Delete a session (Admin only).

    Args:
        session_id: Session to delete
        admin_verified: Admin verification dependency

    Returns:
        Deletion confirmation
    """
    try:
        success = await session_manager.delete_session(session_id)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        logger.info(f"Admin deleted session: {session_id}")

        return {"message": f"Session {session_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete session")