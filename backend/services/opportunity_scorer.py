import logging

logger = logging.getLogger("vinted_intelligence")


def score_opportunity(
    price: float,
    avg_same_condition: float,
    avg_all: float,
    num_similar: int,
) -> dict:
    """Score an opportunity based on how far below average the price is.

    Returns dict with:
        - margin_absolute: how much cheaper than avg same condition (positive = savings)
        - price_vs_avg: percentage below/above average (negative = good deal)
        - score: 'high' | 'medium' | 'low'
    """
    if avg_same_condition > 0:
        margin_absolute = round(avg_same_condition - price, 2)
        price_vs_avg = round(
            ((price - avg_same_condition) / avg_same_condition) * 100, 1
        )
    elif avg_all > 0:
        margin_absolute = round(avg_all - price, 2)
        price_vs_avg = round(((price - avg_all) / avg_all) * 100, 1)
    else:
        margin_absolute = 0
        price_vs_avg = 0

    # Determine score
    # price_vs_avg is negative when price is below average (good)
    if price_vs_avg <= -25 and num_similar >= 5:
        score = "high"
    elif price_vs_avg <= -10 and num_similar >= 3:
        score = "medium"
    else:
        score = "low"

    return {
        "margin_absolute": margin_absolute,
        "price_vs_avg": price_vs_avg,
        "score": score,
    }
