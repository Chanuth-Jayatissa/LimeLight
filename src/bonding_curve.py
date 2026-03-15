"""
Bonding curve pricing module for tokenized startup projects.

All calculations are deterministic and safe (no external inputs to math).
Supports linear and exponential curves.

Formulas to derive curve parameters from a target end price (when all supply is sold):

  Linear:    price = base_price + (tokens_sold * price_increment)
             => price_increment = (end_price - initial_price) / supply

  Exponential: price = base_price * e^(k * tokens_sold)
             => k = ln(end_price / initial_price) / supply
"""
from __future__ import annotations

import math
from typing import Literal

CurveType = Literal["linear", "exponential"]

# Defaults for auto-generated curve params when user omits them
DEFAULT_INITIAL_PRICE = 0.01
DEFAULT_CURVE_TYPE: CurveType = "linear"
DEFAULT_PRICE_MULTIPLIER = 10.0


def get_auto_curve_params(
    supply: float,
    *,
    initial_price: float | None = None,
    curve_type: CurveType | None = None,
    price_multiplier: float = DEFAULT_PRICE_MULTIPLIER,
) -> tuple[float, CurveType, float | None, float | None]:
    """
    Return (initial_price, curve_type, price_increment, k) with defaults applied.
    Use when initial_price, curve_type, price_increment, or k are omitted.
    price_increment and k are derived so that at full supply, price = initial_price * price_multiplier.
    """
    p0 = initial_price if initial_price is not None else DEFAULT_INITIAL_PRICE
    ct = curve_type if curve_type is not None else DEFAULT_CURVE_TYPE
    inc, k_val = derive_curve_params(ct, p0, supply, price_multiplier=price_multiplier)
    return (p0, ct, inc, k_val)


def derive_price_increment_linear(
    initial_price: float,
    supply: float,
    end_price: float,
) -> float:
    """
    Derive price_increment so that when tokens_sold = supply, price = end_price.

    Formula: end_price = initial_price + (supply * price_increment)
             => price_increment = (end_price - initial_price) / supply

    Args:
        initial_price: Token price at tokens_sold = 0.
        supply: Total token supply (tokens_sold at "end").
        end_price: Desired price when all supply is sold.

    Returns:
        price_increment (must be >= 0; end_price should be >= initial_price).
    """
    if supply <= 0:
        raise ValueError("supply must be positive")
    if end_price < initial_price:
        raise ValueError("end_price must be >= initial_price for linear curve")
    return (end_price - initial_price) / supply


def derive_k_exponential(
    initial_price: float,
    supply: float,
    end_price: float,
) -> float:
    """
    Derive k so that when tokens_sold = supply, price = end_price.

    Formula: end_price = initial_price * e^(k * supply)
             => k = ln(end_price / initial_price) / supply

    Args:
        initial_price: Token price at tokens_sold = 0 (must be > 0).
        supply: Total token supply.
        end_price: Desired price when all supply is sold (must be > 0).

    Returns:
        k (growth constant for exponential curve).
    """
    if supply <= 0:
        raise ValueError("supply must be positive")
    if initial_price <= 0 or end_price <= 0:
        raise ValueError("initial_price and end_price must be positive for exponential curve")
    ratio = end_price / initial_price
    return math.log(ratio) / supply


def derive_curve_params(
    curve_type: CurveType,
    initial_price: float,
    supply: float,
    *,
    end_price: float | None = None,
    price_multiplier: float | None = None,
) -> tuple[float | None, float | None]:
    """
    Derive price_increment (linear) or k (exponential) from a target end price or multiplier.

    Use exactly one of end_price or price_multiplier.
    - end_price: absolute price when tokens_sold = supply.
    - price_multiplier: end_price = initial_price * price_multiplier (e.g. 10 => 10x at end).

    Returns:
        (price_increment, k): one is set, the other None, depending on curve_type.
    """
    if end_price is not None and price_multiplier is not None:
        raise ValueError("Provide either end_price or price_multiplier, not both")
    if end_price is None and price_multiplier is None:
        return (None, None)
    if price_multiplier is not None:
        if price_multiplier <= 0:
            raise ValueError("price_multiplier must be positive")
        end_price = initial_price * price_multiplier
    assert end_price is not None
    if curve_type == "linear":
        return (derive_price_increment_linear(initial_price, supply, end_price), None)
    if curve_type == "exponential":
        return (None, derive_k_exponential(initial_price, supply, end_price))
    raise ValueError(f"Unknown curve_type: {curve_type}")


def calculate_price_linear(
    base_price: float,
    tokens_sold: float,
    price_increment: float,
) -> float:
    """
    Linear bonding curve: price = base_price + (tokens_sold * price_increment).

    Args:
        base_price: Starting token price (e.g. in SOL).
        tokens_sold: Total tokens already purchased.
        price_increment: Price growth per token.

    Returns:
        Current price per token.
    """
    if base_price < 0 or tokens_sold < 0 or price_increment < 0:
        raise ValueError("base_price, tokens_sold, and price_increment must be non-negative")
    return base_price + (tokens_sold * price_increment)


def calculate_price_exponential(
    base_price: float,
    tokens_sold: float,
    k: float,
) -> float:
    """
    Exponential bonding curve: price = base_price * e^(k * tokens_sold).

    Args:
        base_price: Starting token price (e.g. in SOL).
        tokens_sold: Total tokens already purchased.
        k: Growth constant.

    Returns:
        Current price per token.
    """
    if base_price <= 0 or tokens_sold < 0 or k < 0:
        raise ValueError("base_price must be positive; tokens_sold and k must be non-negative")
    return base_price * math.exp(k * tokens_sold)


def calculate_purchase_cost(
    curve_type: CurveType,
    base_price: float,
    tokens_sold: float,
    amount: float,
    price_increment: float | None = None,
    k: float | None = None,
) -> tuple[float, float]:
    """
    Calculate total cost to buy `amount` tokens and the price after purchase.

    MVP approximation: cost = current_price * amount (single price at tokens_sold).
    For linear curve, exact cost would be integral; this uses the simpler formula.

    Args:
        curve_type: "linear" or "exponential".
        base_price: Initial token price.
        tokens_sold: Tokens already sold.
        amount: Number of tokens to buy.
        price_increment: Required for linear curve.
        k: Required for exponential curve.

    Returns:
        (total_cost_in_sol, price_per_token_after_purchase)
    """
    if amount <= 0:
        raise ValueError("amount must be positive")

    if curve_type == "linear":
        if price_increment is None:
            raise ValueError("price_increment required for linear curve")
        current_price = calculate_price_linear(base_price, tokens_sold, price_increment)
        price_after = calculate_price_linear(base_price, tokens_sold + amount, price_increment)
    elif curve_type == "exponential":
        if k is None:
            raise ValueError("k required for exponential curve")
        current_price = calculate_price_exponential(base_price, tokens_sold, k)
        price_after = calculate_price_exponential(base_price, tokens_sold + amount, k)
    else:
        raise ValueError(f"Unknown curve_type: {curve_type}")

    # MVP: cost = current_price * amount
    cost = current_price * amount
    return (cost, price_after)


def get_current_price(
    curve_type: CurveType,
    base_price: float,
    tokens_sold: float,
    price_increment: float | None = None,
    k: float | None = None,
) -> float:
    """Get current token price for a project."""
    if curve_type == "linear":
        if price_increment is None:
            raise ValueError("price_increment required for linear curve")
        return calculate_price_linear(base_price, tokens_sold, price_increment)
    if curve_type == "exponential":
        if k is None:
            raise ValueError("k required for exponential curve")
        return calculate_price_exponential(base_price, tokens_sold, k)
    raise ValueError(f"Unknown curve_type: {curve_type}")
