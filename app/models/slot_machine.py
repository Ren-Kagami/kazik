"""
Pydantic models for slot machine game data structures.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
import uuid


class SessionCreate(BaseModel):
    """Request model for creating a new session."""

    initial_credits: int = Field(default=100, ge=1, le=10000)

    class Config:
        schema_extra = {
            "example": {
                "initial_credits": 100
            }
        }


class SessionResponse(BaseModel):
    """Response model for session data."""

    session_id: str = Field(..., description="Unique session identifier")
    credits: int = Field(..., ge=0, description="Current credits")
    created_at: datetime = Field(..., description="Session creation timestamp")
    total_spins: int = Field(default=0, ge=0, description="Total spins performed")
    total_winnings: int = Field(default=0, ge=0, description="Total winnings accumulated")

    class Config:
        schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "credits": 100,
                "created_at": "2025-01-20T10:00:00Z",
                "total_spins": 0,
                "total_winnings": 0
            }
        }


class SpinRequest(BaseModel):
    """Request model for performing a spin."""

    bet_amount: int = Field(..., ge=1, le=100, description="Bet amount for this spin")

    @validator('bet_amount')
    def validate_bet_amount(cls, v):
        if v <= 0:
            raise ValueError('Bet amount must be positive')
        return v

    class Config:
        schema_extra = {
            "example": {
                "bet_amount": 10
            }
        }


class SpinResponse(BaseModel):
    """Response model for spin results."""

    symbols: List[str] = Field(..., description="Resulting symbols from the spin")
    payout: int = Field(..., ge=0, description="Payout amount")
    credits_remaining: int = Field(..., ge=0, description="Credits after spin")
    is_winner: bool = Field(..., description="Whether this spin was a winner")
    session_data: Dict[str, Any] = Field(default_factory=dict, description="Updated session statistics")

    class Config:
        schema_extra = {
            "example": {
                "symbols": ["🍒", "🍒", "🍒"],
                "payout": 20,
                "credits_remaining": 110,
                "is_winner": True,
                "session_data": {
                    "total_spins": 1,
                    "total_winnings": 20,
                    "rtp": 200.0
                }
            }
        }


class SimulationRequest(BaseModel):
    """Request model for running simulations."""

    num_simulations: int = Field(..., ge=100, le=100000, description="Number of spins to simulate")
    bet_amount: int = Field(..., ge=1, le=100, description="Bet amount per spin")

    @validator('num_simulations')
    def validate_num_simulations(cls, v):
        if not (100 <= v <= 100000):
            raise ValueError('Number of simulations must be between 100 and 100,000')
        return v

    class Config:
        schema_extra = {
            "example": {
                "num_simulations": 10000,
                "bet_amount": 10
            }
        }


class SimulationResponse(BaseModel):
    """Response model for simulation results."""

    simulation_stats: Dict[str, Any] = Field(..., description="Detailed simulation statistics")
    comparison_data: Dict[str, float] = Field(..., description="Comparison with theoretical values")

    class Config:
        schema_extra = {
            "example": {
                "simulation_stats": {
                    "total_spins": 10000,
                    "total_bet": 100000,
                    "total_payout": 95000,
                    "win_rate": 25.5,
                    "actual_rtp": 95.0,
                    "biggest_win": 500
                },
                "comparison_data": {
                    "theoretical_rtp": 94.5,
                    "actual_rtp": 95.0,
                    "rtp_difference": 0.5
                }
            }
        }


class SessionStats(BaseModel):
    """Model for session statistics."""

    session_id: str = Field(..., description="Session identifier")
    created_at: datetime = Field(..., description="Session creation time")
    total_spins: int = Field(..., ge=0, description="Total spins in session")
    total_winnings: int = Field(..., ge=0, description="Total winnings in session")
    final_credits: int = Field(..., ge=0, description="Final credits in session")
    estimated_rtp: float = Field(..., ge=0.0, le=1000.0, description="Estimated RTP for session")

    class Config:
        schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-01-20T10:00:00Z",
                "total_spins": 50,
                "total_winnings": 475,
                "final_credits": 125,
                "estimated_rtp": 95.0
            }
        }


class GameSession(BaseModel):
    """Internal model for game session data."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    credits: int = Field(..., ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    total_spins: int = Field(default=0, ge=0)
    total_winnings: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)

    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def add_spin_result(self, bet_amount: int, payout: int):
        """Add results from a spin to session stats."""
        self.credits = self.credits - bet_amount + payout
        self.total_spins += 1
        self.total_winnings += payout
        self.update_activity()

    class Config:
        schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "credits": 150,
                "created_at": "2025-01-20T10:00:00Z",
                "last_activity": "2025-01-20T10:05:00Z",
                "total_spins": 10,
                "total_winnings": 50,
                "is_active": True
            }
        }


# Admin models
class AdminProbabilityUpdate(BaseModel):
    """Model for updating probability settings via admin panel."""

    symbol_weights: Dict[str, int] = Field(
        ...,
        description="Mapping of symbols to their weights"
    )
    payout_multipliers: Dict[str, int] = Field(
        ...,
        description="Mapping of symbols to their payout multipliers"
    )

    @validator('symbol_weights')
    def validate_symbol_weights(cls, v):
        if not v:
            raise ValueError('Symbol weights cannot be empty')

        for symbol, weight in v.items():
            if not isinstance(weight, int) or weight <= 0:
                raise ValueError(f'Weight for symbol {symbol} must be a positive integer')

        total_weight = sum(v.values())
        if not (50 <= total_weight <= 200):
            raise ValueError('Total weight must be between 50 and 200')

        return v

    @validator('payout_multipliers')
    def validate_payout_multipliers(cls, v):
        if not v:
            raise ValueError('Payout multipliers cannot be empty')

        for symbol, multiplier in v.items():
            if not isinstance(multiplier, int) or multiplier <= 0:
                raise ValueError(f'Multiplier for symbol {symbol} must be a positive integer')
            if multiplier > 100:
                raise ValueError(f'Multiplier for symbol {symbol} cannot exceed 100')

        return v

    class Config:
        schema_extra = {
            "example": {
                "symbol_weights": {
                    "🍒": 30,
                    "🍋": 25,
                    "🍊": 20,
                    "🍇": 15,
                    "🔔": 5,
                    "⭐": 3,
                    "💎": 2
                },
                "payout_multipliers": {
                    "🍒": 2,
                    "🍋": 3,
                    "🍊": 4,
                    "🍇": 5,
                    "🔔": 10,
                    "⭐": 20,
                    "💎": 50
                }
            }
        }


class AdminLoginRequest(BaseModel):
    """Request model for admin authentication."""

    username: str = Field(..., min_length=1, description="Admin username")
    password: str = Field(..., min_length=1, description="Admin password")

    class Config:
        schema_extra = {
            "example": {
                "username": "admin",
                "password": "secure_password_123"
            }
        }


class AdminLoginResponse(BaseModel):
    """Response model for admin authentication."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Detailed error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Bet amount must be positive",
                "timestamp": "2025-01-20T10:00:00Z"
            }
        }