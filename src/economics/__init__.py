"""Economics subpackage: ROI, Market rolling stats, and Evaluators."""

from economics.economy import (
    affordable_hires,
    best_crop,
    crop_roi,
    next_quadrant_target,
    should_buy_seed,
    should_expand,
)
from economics.evaluators import (
    evaluate_expansion,
    evaluate_livestock,
    evaluate_market,
)
from economics.market import Market

__all__ = [
    "Market",
    "affordable_hires",
    "best_crop",
    "crop_roi",
    "evaluate_expansion",
    "evaluate_livestock",
    "evaluate_market",
    "next_quadrant_target",
    "should_buy_seed",
    "should_expand",
]
