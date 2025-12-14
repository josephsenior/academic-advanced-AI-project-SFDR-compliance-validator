"""
Fund Changes Compliance Rules

Rules for handling fund changes (name, strategy, benchmark, etc.).
"""

from dataclasses import dataclass


@dataclass
class FundChangesRules:
    """Rules for funds with changes (benchmark, strategy, risk profile)"""
    
    # Change notification
    MUST_INDICATE_CHANGE_NATURE_AND_DATE: bool = True
    MUST_KEEP_PAST_PERFORMANCE: bool = True
    
    # Post-change performance
    CAN_SHOW_ONLY_POST_CHANGE_IF_MORE_THAN_1_YEAR: bool = True
    DEDICATED_FUNDS_EXCLUDED_FROM_POST_CHANGE_RULE: bool = True
    
    # Benchmark display
    BENCHMARK_ACCORDING_TO_PROSPECTUS: bool = True  # e.g., dividends included
    
    # Merger rules
    MERGER_CAN_USE_ABSORBED_HISTORY_IF: bool = True  # Conditions below
    MERGER_ABSORBING_CREATED_BY_MERGER: bool = True
    MERGER_SAME_STRATEGY: bool = True
    MERGER_SAME_OBJECTIVE: bool = True
    MERGER_SAME_TEAM: bool = True
    MERGER_SAME_COST_STRUCTURE: bool = True

