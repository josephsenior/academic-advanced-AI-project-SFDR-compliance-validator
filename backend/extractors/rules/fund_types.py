"""
Fund Type-Specific Compliance Rules

Rules for strategy presentations, dated funds, and private equity funds.
"""

from dataclasses import dataclass


@dataclass
class StrategyRules:
    """Rules for strategy presentations (professional clients only)"""
    
    # Client restriction
    PROFESSIONAL_ONLY: bool = True
    
    # Performance display
    CAN_SHOW_GROSS_PERFORMANCE: bool = True
    CAN_SHOW_BACKTEST: bool = True
    CAN_SHOW_SIMULATION: bool = True
    
    # Track record
    CAN_SHOW_STRATEGY_TRACK_RECORD: bool = True
    CAN_SHOW_TEAM_TRACK_RECORD: bool = True


@dataclass
class DatedFundRules:
    """Rules for dated/target date funds"""
    
    # Active management dated funds - Retail
    ACTIVE_NO_YTM_FOR_RETAIL: bool = True
    ACTIVE_NO_YTW_FOR_RETAIL: bool = True
    
    # Buy and hold dated funds - Retail
    BUY_HOLD_CAN_SHOW_YTM: bool = True
    BUY_HOLD_CAN_SHOW_YTW: bool = True
    
    # Professional clients
    PROFESSIONAL_NO_RESTRICTION: bool = True


@dataclass
class PrivateEquityRules:
    """Rules for Private Equity funds"""
    
    # Net IRR display
    NET_IRR_ONLY_FOR_PROFESSIONAL_DURING_LIFE: bool = True
    NO_NET_IRR_FOR_RETAIL_BEFORE_MATURITY: bool = True
    NO_INSTITUTIONAL_TRACK_RECORD_FOR_RETAIL: bool = True

