"""
Securities Mention Compliance Rules

Section 4.2 - Rules for mentioning securities in presentations.
"""

from dataclasses import dataclass


@dataclass
class SecuritiesMentionRules:
    """Section 4.2 - Rules for mentioning securities in presentations"""
    
    # PROHIBITED actions
    NO_INVESTMENT_RECOMMENDATIONS: bool = True
    NO_VALUATION_MENTIONS: bool = True  # undervalued/overvalued
    NO_INVESTMENT_STRATEGY_SUGGESTIONS: bool = True
    NO_SECURITIES_COMPARISON: bool = True
    NO_MULTIPLE_MENTIONS_SAME_SECURITY: bool = True
    NO_FUTURE_PROJECTIONS_FOR_SECURITIES: bool = True
    NO_OPINION_ON_CURRENT_FUTURE_VALUE: bool = True
    NO_BUY_SELL_REINFORCE: bool = True
    NO_SPECIFIC_ANALYSIS_ON_SECURITY: bool = True
    NO_FAVORABLE_UNFAVORABLE_OPINION: bool = True
    
    # Prohibited phrases (investment recommendations)
    RECOMMENDATION_PHRASES = [
        "acheter", "buy", "kaufen",
        "vendre", "sell", "verkaufen",
        "renforcer", "reinforce", "verstärken",
        "sous-évalué", "undervalued", "unterbewertet",
        "surévalué", "overvalued", "überbewertet",
        "correctement évalué", "correctly valued", "korrekt bewertet",
        "nous recommandons", "we recommend", "wir empfehlen",
        "à notre avis", "in our opinion", "unserer Meinung nach",
        "selon nous", "according to us", "nach unserer Einschätzung"
    ]
    
    # ALLOWED mentions
    ALLOWED_MARKET_TRENDS: bool = True
    ALLOWED_MACRO_INDICATORS: bool = True  # FX rates, interest rates, commodities
    ALLOWED_GENERAL_SECTORS: bool = True
    ALLOWED_FACTUAL_INFO: bool = True  # Recent events, public announcements
    ALLOWED_PORTFOLIO_HOLDINGS_WITH_PAST_PERF: bool = True
    ALLOWED_ILLUSTRATIVE_EXAMPLES: bool = True  # Without projections
    
    # Interview rules
    INTERVIEW_ONLY_PUBLIC_FACTS: bool = True
    INTERVIEW_CAN_COMMENT_HISTORICAL: bool = True
    INTERVIEW_NO_CURRENT_FUTURE_VALUE_OPINION: bool = True

