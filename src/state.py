"""
Project state and JSON storage for tokenized startup projects.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .bonding_curve import CurveType

# Fixed limited supply per project (bonding curve applies to this cap)
FIXED_SUPPLY = 100_000

STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "projects.json"


def _ensure_data_dir() -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_state() -> dict[str, Any]:
    _ensure_data_dir()
    if not STATE_FILE.exists():
        return {"projects": [], "next_id": 1}
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_state(state: dict[str, Any]) -> None:
    _ensure_data_dir()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def create_project(
    name: str,
    description: str,
    github: str,
    supply: int,
    initial_price: float,
    curve_type: CurveType,
    price_increment: float | None = None,
    k: float | None = None,
) -> dict[str, Any]:
    """Create a new project and persist it."""
    state = _load_state()
    pid = state["next_id"]
    state["next_id"] = pid + 1
    project = {
        "id": pid,
        "name": name,
        "description": description,
        "github": github,
        "supply": supply,
        "initial_price": initial_price,
        "curve_type": curve_type,
        "price_increment": price_increment,
        "k": k,
        "tokens_sold": 0,
        "treasury_balance": 0.0,
        "active": False,
        "stake_deposited": False,
        "mint_address": None,
        "vault_owner": None,
        "token_name": None,
        "token_symbol": None,
        "token_uri": None,
        "token_description": None,
        "token_image": None,
        "token_external_url": None,
    }
    state["projects"].append(project)
    _save_state(state)
    return project


def get_project(project_id: int) -> dict[str, Any] | None:
    """Get project by id."""
    state = _load_state()
    for p in state["projects"]:
        if p["id"] == project_id:
            return p
    return None


def list_projects() -> list[dict[str, Any]]:
    """List all projects."""
    return _load_state().get("projects", [])


def set_project_token_metadata(
    project_id: int,
    token_name: str | None = None,
    token_symbol: str | None = None,
    token_uri: str | None = None,
    token_description: str | None = None,
    token_image: str | None = None,
    token_external_url: str | None = None,
) -> dict[str, Any] | None:
    """Update token metadata for a project (name, symbol, uri, icon, etc.)."""
    state = _load_state()
    for p in state["projects"]:
        if p["id"] == project_id:
            if token_name is not None:
                p["token_name"] = token_name
            if token_symbol is not None:
                p["token_symbol"] = token_symbol
            if token_uri is not None:
                p["token_uri"] = token_uri
            if token_description is not None:
                p["token_description"] = token_description
            if token_image is not None:
                p["token_image"] = token_image
            if token_external_url is not None:
                p["token_external_url"] = token_external_url
            _save_state(state)
            return p
    return None


def set_project_mint(project_id: int, mint_address: str, vault_owner: str | None = None) -> dict[str, Any] | None:
    """Store the SPL mint address and optional vault owner (pubkey that holds the pre-minted supply)."""
    state = _load_state()
    for p in state["projects"]:
        if p["id"] == project_id:
            p["mint_address"] = mint_address
            if vault_owner is not None:
                p["vault_owner"] = vault_owner
            _save_state(state)
            return p
    return None


def delete_project(project_id: int) -> bool:
    """Remove a project from state. Returns True if deleted, False if not found. Does not touch on-chain data."""
    state = _load_state()
    for i, p in enumerate(state["projects"]):
        if p["id"] == project_id:
            state["projects"].pop(i)
            _save_state(state)
            return True
    return False


def update_project_tokens_and_treasury(
    project_id: int,
    tokens_sold_delta: int,
    treasury_delta: float,
) -> dict[str, Any] | None:
    """Update tokens_sold and treasury_balance for a project."""
    state = _load_state()
    for p in state["projects"]:
        if p["id"] == project_id:
            p["tokens_sold"] = p["tokens_sold"] + tokens_sold_delta
            p["treasury_balance"] = round(p["treasury_balance"] + treasury_delta, 10)
            _save_state(state)
            return p
    return None
