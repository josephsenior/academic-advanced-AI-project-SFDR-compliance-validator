"""
Disclaimer Compliance Rules

Rules for disclaimers including performance, backtest, and simulation disclaimers.
"""

from dataclasses import dataclass


@dataclass
class DisclaimerRules:
    """Disclaimer requirements and text"""
    
    # Position requirement
    MUST_BE_BELOW_OR_BESIDE_PERFORMANCE: bool = True
    MUST_BE_READABLE: bool = True
    
    # Past performance disclaimer (required always)
    PAST_PERFORMANCE_DISCLAIMER_FR = "les performances passées ne présagent pas des performances futures et ne sont pas constantes dans le temps"
    PAST_PERFORMANCE_DISCLAIMER_EN = "past performance is not a reliable indication of future return and is not constant over time"
    PAST_PERFORMANCE_DISCLAIMER_DE = "Historische Wertentwicklungen, Simulationen oder Prognosen sind kein verlässlicher Indikator für künftige Wertentwicklungen und unterliegen im Zeitverlauf Schwankungen"
    
    # Backtest disclaimer (professional only, France only)
    BACKTEST_DISCLAIMER_FR = """Les chiffres se réfèrent à des simulations des performances passées. Ces simulations sont le résultat d'estimations d'OBAM SAS à un moment donné, sur la base de paramètres sélectionnés par Oddo BHF Asset Management, de conditions de marché à ce moment donné et de données historiques qui ne préjugent en rien de résultats futurs. En conséquence, ces simulations n'ont qu'une valeur indicative et ne sauraient constituer en aucune manière une promesse de rendement."""
    BACKTEST_DISCLAIMER_EN = """The figures refer to simulations of past performances. These simulations are the result of estimates by ODDO BHF AM at a given moment on the basis of parameters selected by ODDO BHF AM SAS/GmbH/Lux, market conditions at this given moment and historical data that are not a guide to future results. As a result, these simulations only have an indicative value and do not in any case constitute a promised return"""
    
    # Future simulation disclaimer
    FUTURE_SIMULATION_DISCLAIMER_FR = """La simulation présentée ne constitue pas une prévision de la performance future de vos investissements. Elle a seulement pour but d'illustrer les mécanismes de votre investissement sur la durée de placement. L'évolution de la valeur de votre investissement pourra s'écarter de ce qui est affiché, à la hausse comme à la baisse."""
    FUTURE_SIMULATION_DISCLAIMER_EN = """The simulation presented does not constitute a forecast of the future performance of your investments. It is solely designed to illustrate the mechanisms of your investment over the investment period. The value of your investment may deviate upwards or downwards from what is displayed."""
    
    # Multiple scenarios disclaimer (add to future simulation)
    MULTIPLE_SCENARIOS_DISCLAIMER_FR = """Les gains et les pertes peuvent dépasser les montants affichés, respectivement, dans les scénarios les plus favorables et les plus défavorables. En poursuivant, vous reconnaissez avoir pris connaissance de cet avertissement, l'avoir compris et en accepter le contenu."""
    MULTIPLE_SCENARIOS_DISCLAIMER_EN = """Gains and losses may exceed the presented amounts in respectively the most favourable and unfavourable scenarios. By continuing, you acknowledge that you have taken note of this disclaimer, have understood it and accept the content."""
    
    # Past simulation disclaimer
    PAST_SIMULATION_DISCLAIMER_FR = """Les performances affichées ne représentent pas les performances réelles de la part X sur une période donnée. Elles sont issues de simulations calculées par la société de gestion à partir des performances de la part Y du même fonds, retraitées des frais de gestion fixes, des frais de gestion variables, devises"""
    
    # Merger disclaimer
    MERGER_DISCLAIMER_TEMPLATE = """les performances présentées sont celles du Fonds « {absorbed_fund} » (de droit {jurisdiction} - lancé le {launch_date}) qui a été absorbé par le fonds « {absorbing_fund} » en date du {merger_date}. « {absorbing_fund} » poursuit exactement la même stratégie d'investissement et le même objectif de gestion que le fonds « {absorbed_fund} ». L'équipe de gestion et la structure des coûts restent inchangées."""


@dataclass
class SimulationRules:
    """Rules for performance simulations"""
    
    # Future performance simulation
    FUTURE_NOT_BASED_ON_PAST_SIMULATIONS: bool = True
    FUTURE_BASED_ON_REASONABLE_HYPOTHESES: bool = True
    FUTURE_GROSS_MUST_SHOW_FEE_IMPACT: bool = True
    FUTURE_REALISTIC_MARKET_HYPOTHESES: bool = True
    FUTURE_CONSISTENT_VOLATILITY: bool = True
    FUTURE_CONSISTENT_WITH_HORIZON: bool = True
    
    # Past performance simulation
    PAST_ONLY_FOR_NEW_SHARE_CLASS: bool = True
    PAST_BASED_ON_EXISTING_SHARE: bool = True
    PAST_SHARE_PROPORTION_MUST_NOT_DIFFER_MUCH: bool = True
    PAST_EXISTING_SHARE_SIMULATION_PROHIBITED: bool = True
    PAST_MUST_RECALCULATE_FEES: bool = True

