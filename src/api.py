"""
FastAPI server for Startup CLI — use from your frontend webapp.

All project/buy/sell state and Solana Devnet operations are exposed as REST endpoints.
Enable CORS for your frontend origin.
"""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import state
from .addresses import get_project_addresses
from .bonding_curve import (
    DEFAULT_INITIAL_PRICE,
    DEFAULT_CURVE_TYPE,
    calculate_purchase_cost,
    derive_curve_params,
    get_current_price,
)
from .ipfs_upload import get_devnet_mint_url, upload_to_ipfs
from .solana_mint import (
    build_unsigned_sell_transaction,
    create_mint_for_project,
    get_client,
    get_client_devnet,
    get_platform_keypair,
    load_keypair_from_base64,
    mint_tokens_to_buyer,
    submit_signed_transaction,
    transfer_tokens_to_vault,
)
from .state import set_project_mint, set_project_token_metadata, update_project_tokens_and_treasury
from .token_metadata import write_metadata_json

from solders.pubkey import Pubkey

# --- Pydantic models ---

class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""
    github: str = "https://github.com"
    supply: int = Field(default=100_000, ge=1)
    initial_price: float | None = Field(default=None, gt=0, description="Initial token price (SOL). Omit to use default 0.01.")
    curve_type: Literal["linear", "exponential"] | None = Field(default=None, description="Omit to use default 'linear'.")
    price_increment: float | None = Field(default=None, ge=0, description="Linear only. Omit to derive from target_end_price or price_multiplier (default 10x at full supply).")
    k: float | None = Field(default=None, ge=0, description="Exponential only. Omit to derive from target_end_price or price_multiplier.")
    target_end_price: float | None = Field(default=None, gt=0, description="Target price when supply is fully sold. Used to derive price_increment (linear) or k (exponential) when those are omitted.")
    price_multiplier: float | None = Field(default=None, gt=0, description="End price = initial_price * this when curve params omitted (default 10). Used to derive price_increment or k.")
    token_name: str | None = None
    token_symbol: str | None = None
    token_uri: str | None = None
    token_description: str | None = None
    token_image: str | None = None
    token_external_url: str | None = None
    upload_to_ipfs: bool = False
    create_mint: bool = Field(default=True, description="If True, create SPL mint and set vault (requires PLATFORM_KEYPAIR in env)")
    vault_owner: str | None = Field(default=None, description="Solana address that will hold the pre-minted supply. Omit to use platform wallet (PLATFORM_KEYPAIR) as vault.")


class CreateMintRequest(BaseModel):
    keypair_base64: str | None = Field(default=None, description="Optional. If omitted, use PLATFORM_KEYPAIR from env")
    vault_owner: str | None = Field(default=None, description="Solana address to hold the pre-minted supply. Omit to use platform wallet as vault.")
    token_name: str | None = None
    token_symbol: str | None = None
    token_uri: str | None = None


class BuyTokensRequest(BaseModel):
    amount: int = Field(..., gt=0)
    buyer_pubkey: str = Field(..., description="Wallet address that will receive the tokens (e.g. from Phantom)")
    keypair_base64: str | None = Field(default=None, description="Optional. If omitted, use PLATFORM_KEYPAIR from env (mint authority)")


class SellPrepareRequest(BaseModel):
    amount: int = Field(..., gt=0)
    seller_pubkey: str


class SellConfirmRequest(BaseModel):
    signed_transaction_base64: str
    amount: int = Field(..., gt=0, description="Number of tokens sold (for state update)")


class SellWithKeypairRequest(BaseModel):
    amount: int = Field(..., gt=0)
    keypair_base64: str


class GenerateMetadataRequest(BaseModel):
    project_id: int | None = None
    name: str | None = None
    symbol: str | None = None
    description: str = ""
    image: str = ""
    external_url: str = ""
    output_path: str | None = None
    upload_to_ipfs: bool = False


# --- App ---

app = FastAPI(
    title="Startup CLI API",
    description="REST API for tokenized startup projects on Solana Devnet (bonding curve, mint, buy, sell).",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_project(project_id: int) -> dict[str, Any]:
    p = state.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return p


# --- Projects ---

@app.get("/projects")
def list_projects() -> list[dict[str, Any]]:
    """List all projects."""
    return state.list_projects()


@app.get("/projects/{project_id}")
def get_project(project_id: int) -> dict[str, Any]:
    """Get a single project by ID."""
    return _get_project(project_id)


@app.post("/projects")
def create_project(body: CreateProjectRequest) -> dict[str, Any]:
    """Create a new project. initial_price, curve_type, price_increment, and k are optional and auto-generated if omitted (defaults: 0.01 SOL, linear, 10x at full supply)."""
    initial_price = body.initial_price if body.initial_price is not None else DEFAULT_INITIAL_PRICE
    curve_type = body.curve_type if body.curve_type is not None else DEFAULT_CURVE_TYPE
    price_increment = body.price_increment
    k = body.k
    if (curve_type == "linear" and price_increment is None) or (curve_type == "exponential" and k is None):
        end_price = body.target_end_price
        mult = body.price_multiplier
        if end_price is None and mult is None:
            mult = 10.0
        try:
            inc, k_derived = derive_curve_params(
                curve_type,
                initial_price,
                float(body.supply),
                end_price=end_price,
                price_multiplier=mult,
            )
            if inc is not None:
                price_increment = inc
            if k_derived is not None:
                k = k_derived
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    if curve_type == "linear" and price_increment is None:
        raise HTTPException(status_code=400, detail="Set price_increment or target_end_price or price_multiplier for linear curve")
    if curve_type == "exponential" and k is None:
        raise HTTPException(status_code=400, detail="Set k or target_end_price or price_multiplier for exponential curve")
    project = state.create_project(
        name=body.name,
        description=body.description,
        github=body.github,
        supply=body.supply,
        initial_price=initial_price,
        curve_type=curve_type,
        price_increment=price_increment,
        k=k,
    )
    pid = project["id"]
    t_name = body.token_name or body.name
    t_symbol = body.token_symbol or "".join(c[0].upper() for c in body.name.split() if c)[:10] or "TKN"
    state.set_project_token_metadata(
        pid,
        token_name=t_name,
        token_symbol=t_symbol,
        token_uri=body.token_uri,
        token_description=body.token_description or body.description,
        token_image=body.token_image,
        token_external_url=body.token_external_url or body.github,
    )
    if body.upload_to_ipfs and not body.token_uri:
        try:
            data_dir = Path(state.STATE_FILE).parent
            # Upload full metadata JSON to IPFS: name, symbol, description, image, external_url (all from request)
            meta_path = write_metadata_json(
                data_dir / f"metadata_{pid}.json",
                name=t_name,
                symbol=t_symbol,
                description=body.token_description or body.description or "",
                image=body.token_image or "",
                external_url=body.token_external_url or body.github or "",
            )
            token_uri = upload_to_ipfs(meta_path)
            state.set_project_token_metadata(pid, token_uri=token_uri)
            project = state.get_project(pid) or project
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"IPFS upload failed: {e}")

    if body.create_mint:
        kp = get_platform_keypair()
        if not kp:
            raise HTTPException(
                status_code=503,
                detail="create_mint is True but PLATFORM_KEYPAIR_BASE64 or PLATFORM_KEYPAIR_PATH is not set. Set one in env to create mint automatically.",
            )
        p = state.get_project(pid) or project
        name = body.token_name or t_name
        symbol = body.token_symbol or t_symbol
        uri = body.token_uri or p.get("token_uri")
        supply = p.get("supply", 100_000) or 100_000
        vault_owner_pubkey = Pubkey.from_string(body.vault_owner) if body.vault_owner else None
        resolved_vault_owner = (body.vault_owner if body.vault_owner else str(kp.pubkey()))
        conn = get_client()
        try:
            mint_address = create_mint_for_project(
                conn, kp,
                token_name=name,
                token_symbol=symbol,
                token_uri=uri,
                initial_supply=supply,
                vault_owner_pubkey=vault_owner_pubkey,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Create mint failed: {e}")
        set_project_mint(pid, mint_address, vault_owner=resolved_vault_owner)
        if name or symbol or uri:
            set_project_token_metadata(pid, token_name=name, token_symbol=symbol, token_uri=uri)
        project = state.get_project(pid) or project

    return state.get_project(pid) or project


@app.delete("/projects/{project_id}")
def delete_project(project_id: int) -> dict[str, str]:
    """Delete a project from local state (on-chain data is not removed)."""
    _get_project(project_id)
    if not state.delete_project(project_id):
        raise HTTPException(status_code=500, detail="Delete failed")
    return {"status": "deleted", "project_id": str(project_id)}


# --- Price & addresses ---

@app.get("/projects/{project_id}/price")
def get_price(project_id: int, amount: int | None = None) -> dict[str, Any]:
    """Get current token price. If amount is set, also return cost and price_after."""
    p = _get_project(project_id)
    current = get_current_price(
        curve_type=p["curve_type"],
        base_price=p["initial_price"],
        tokens_sold=p["tokens_sold"],
        price_increment=p.get("price_increment"),
        k=p.get("k"),
    )
    out: dict[str, Any] = {"current_price_sol": current, "tokens_sold": p["tokens_sold"], "supply": p["supply"]}
    if amount is not None and amount > 0:
        if p["tokens_sold"] + amount > p["supply"]:
            raise HTTPException(status_code=400, detail="Not enough tokens remaining")
        cost, price_after = calculate_purchase_cost(
            curve_type=p["curve_type"],
            base_price=p["initial_price"],
            tokens_sold=p["tokens_sold"],
            amount=amount,
            price_increment=p.get("price_increment"),
            k=p.get("k"),
        )
        out["amount"] = amount
        out["cost_sol"] = cost
        out["price_after_sol"] = price_after
    return out


@app.get("/projects/{project_id}/addresses")
def get_addresses(project_id: int) -> dict[str, str]:
    """Get project account, treasury, mint, and vault_owner addresses."""
    p = _get_project(project_id)
    project_addr, treasury_addr = get_project_addresses(project_id)
    return {
        "project_account": project_addr,
        "treasury": treasury_addr,
        "mint": p.get("mint_address") or "",
        "vault_owner": p.get("vault_owner") or "",
    }


@app.get("/projects/{project_id}/vault")
def get_vault(project_id: int) -> dict[str, str]:
    """Get vault address (and mint) for a project by ID. Use for sell flow: vault is where tokens go when user sells."""
    p = _get_project(project_id)
    return {
        "vault_owner": p.get("vault_owner") or "",
        "mint": p.get("mint_address") or "",
    }


# --- Create mint ---

@app.post("/projects/{project_id}/mint")
def create_mint(project_id: int, body: CreateMintRequest) -> dict[str, str]:
    """Create SPL token mint on Devnet and pre-mint supply to vault. Uses keypair_base64 if provided, else PLATFORM_KEYPAIR from env."""
    p = _get_project(project_id)
    if body.keypair_base64:
        try:
            kp = load_keypair_from_base64(body.keypair_base64)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid keypair_base64: {e}")
    else:
        kp = get_platform_keypair()
        if not kp:
            raise HTTPException(status_code=503, detail="Set PLATFORM_KEYPAIR_BASE64 or PLATFORM_KEYPAIR_PATH in env, or send keypair_base64 in body.")
    name = body.token_name or p.get("token_name")
    symbol = body.token_symbol or p.get("token_symbol")
    uri = body.token_uri or p.get("token_uri")
    supply = p.get("supply", 100_000) or 100_000
    vault_owner_pubkey = Pubkey.from_string(body.vault_owner) if body.vault_owner else None
    resolved_vault_owner = (body.vault_owner if body.vault_owner else str(kp.pubkey()))
    conn = get_client()
    try:
        mint_address = create_mint_for_project(
            conn, kp,
            token_name=name,
            token_symbol=symbol,
            token_uri=uri,
            initial_supply=supply,
            vault_owner_pubkey=vault_owner_pubkey,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    set_project_mint(project_id, mint_address, vault_owner=resolved_vault_owner)
    if name or symbol or uri:
        set_project_token_metadata(project_id, token_name=name, token_symbol=symbol, token_uri=uri)
    return {
        "mint_address": mint_address,
        "explorer_url": get_devnet_mint_url(mint_address),
    }


# --- Buy tokens ---

@app.post("/projects/{project_id}/buy")
def buy_tokens(project_id: int, body: BuyTokensRequest) -> dict[str, str]:
    """Buy project tokens: transfer from vault to buyer. Uses keypair_base64 if provided, else PLATFORM_KEYPAIR from env. User only needs to send buyer_pubkey (e.g. from Phantom)."""
    p = _get_project(project_id)
    mint_addr = p.get("mint_address")
    if not mint_addr:
        raise HTTPException(status_code=400, detail="Project has no mint; create mint first")
    if p["tokens_sold"] + body.amount > p["supply"]:
        raise HTTPException(status_code=400, detail="Not enough tokens remaining")
    try:
        cost, _ = calculate_purchase_cost(
            curve_type=p["curve_type"],
            base_price=p["initial_price"],
            tokens_sold=p["tokens_sold"],
            amount=body.amount,
            price_increment=p.get("price_increment"),
            k=p.get("k"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if body.keypair_base64:
        try:
            kp = load_keypair_from_base64(body.keypair_base64)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid keypair_base64: {e}")
    else:
        kp = get_platform_keypair()
        if not kp:
            raise HTTPException(status_code=503, detail="Set PLATFORM_KEYPAIR_BASE64 or PLATFORM_KEYPAIR_PATH in env, or send keypair_base64 in body.")
    vault_owner = p.get("vault_owner")
    if vault_owner and str(kp.pubkey()) != vault_owner:
        raise HTTPException(
            status_code=400,
            detail="Project has custom vault_owner; send the vault owner's keypair as keypair_base64 to perform buy.",
        )
    vault_owner_pubkey = Pubkey.from_string(vault_owner) if vault_owner else None
    vault_signer_keypair = kp if vault_owner_pubkey else None
    conn = get_client()
    try:
        sig = mint_tokens_to_buyer(
            conn, mint_addr, Pubkey.from_string(body.buyer_pubkey), body.amount, kp, kp,
            vault_owner_pubkey=vault_owner_pubkey,
            vault_signer_keypair=vault_signer_keypair,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    update_project_tokens_and_treasury(project_id, body.amount, cost)
    return {"signature": sig, "buyer": body.buyer_pubkey}


# --- Sell: prepare (unsigned tx for Phantom) and confirm (submit signed tx) ---

@app.post("/projects/{project_id}/sell/prepare")
def sell_prepare(project_id: int, body: SellPrepareRequest) -> dict[str, Any]:
    """Prepare a sell: returns unsigned transaction (base64) for the frontend to sign with Phantom, then POST to /sell/confirm."""
    p = _get_project(project_id)
    mint_addr = p.get("mint_address")
    vault_owner = p.get("vault_owner")
    if not mint_addr:
        raise HTTPException(status_code=400, detail="Project has no mint")
    if not vault_owner:
        raise HTTPException(status_code=400, detail="Project has no vault_owner")
    if p["tokens_sold"] < body.amount:
        raise HTTPException(status_code=400, detail="Cannot sell more than tokens_sold")
    conn = get_client_devnet()
    try:
        tx_bytes = build_unsigned_sell_transaction(
            conn,
            mint_address=mint_addr,
            seller_pubkey=Pubkey.from_string(body.seller_pubkey),
            amount=body.amount,
            vault_owner_pubkey=Pubkey.from_string(vault_owner),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    sell_value = get_current_price(
        curve_type=p["curve_type"],
        base_price=p["initial_price"],
        tokens_sold=p["tokens_sold"],
        price_increment=p.get("price_increment"),
        k=p.get("k"),
    ) * body.amount
    tx_b64 = base64.standard_b64encode(tx_bytes).decode("ascii")
    return {
        "unsigned_transaction_base64": tx_b64,
        "amount": body.amount,
        "seller_pubkey": body.seller_pubkey,
        "sell_value_sol_approx": sell_value,
    }


@app.post("/projects/{project_id}/sell/confirm")
def sell_confirm(project_id: int, body: SellConfirmRequest) -> dict[str, Any]:
    """Submit signed sell transaction (from Phantom) and update local state. Send amount for tokens_sold/treasury update."""
    p = _get_project(project_id)
    try:
        signed_bytes = base64.standard_b64decode(body.signed_transaction_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid signed_transaction_base64: {e}")
    if p["tokens_sold"] < body.amount:
        raise HTTPException(status_code=400, detail="amount exceeds tokens_sold")
    sell_value = get_current_price(
        curve_type=p["curve_type"],
        base_price=p["initial_price"],
        tokens_sold=p["tokens_sold"],
        price_increment=p.get("price_increment"),
        k=p.get("k"),
    ) * body.amount
    conn = get_client_devnet()
    try:
        sig = submit_signed_transaction(conn, signed_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    update_project_tokens_and_treasury(project_id, -body.amount, -sell_value)
    return {"signature": sig, "amount": body.amount, "sell_value_sol_approx": sell_value}


@app.post("/projects/{project_id}/sell")
def sell_with_keypair(project_id: int, body: SellWithKeypairRequest) -> dict[str, Any]:
    """Sell tokens using keypair (server signs). For Phantom flow use /sell/prepare + /sell/confirm."""
    p = _get_project(project_id)
    mint_addr = p.get("mint_address")
    vault_owner = p.get("vault_owner")
    if not mint_addr or not vault_owner:
        raise HTTPException(status_code=400, detail="Project must have mint and vault_owner")
    if p["tokens_sold"] < body.amount:
        raise HTTPException(status_code=400, detail="Cannot sell more than tokens_sold")
    try:
        kp = load_keypair_from_base64(body.keypair_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid keypair_base64: {e}")
    sell_value = get_current_price(
        curve_type=p["curve_type"],
        base_price=p["initial_price"],
        tokens_sold=p["tokens_sold"],
        price_increment=p.get("price_increment"),
        k=p.get("k"),
    ) * body.amount
    conn = get_client_devnet()
    try:
        sig = transfer_tokens_to_vault(
            conn,
            mint_address=mint_addr,
            seller_pubkey=kp.pubkey(),
            amount=body.amount,
            seller_keypair=kp,
            payer=kp,
            vault_owner_pubkey=Pubkey.from_string(vault_owner),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    update_project_tokens_and_treasury(project_id, -body.amount, -sell_value)
    return {"signature": sig, "amount": body.amount, "sell_value_sol_approx": sell_value}


# --- Token metadata ---

@app.post("/token-metadata")
def generate_token_metadata(body: GenerateMetadataRequest) -> dict[str, Any]:
    """Generate token metadata JSON. Optionally upload to IPFS and return token_uri."""
    if body.project_id is not None:
        p = state.get_project(body.project_id)
        name = body.name or (p.get("token_name") or p.get("name") if p else None)
        symbol = body.symbol or (p.get("token_symbol") if p else None)
        description = body.description or (p.get("token_description") or p.get("description") if p else "") or ""
        image = body.image or (p.get("token_image") if p else "") or ""
        external_url = body.external_url or (p.get("token_external_url") or p.get("github") if p else "") or ""
        out_path = body.output_path or str(Path(state.STATE_FILE).parent / f"metadata_{body.project_id}.json")
    else:
        if not body.name or not body.symbol:
            raise HTTPException(status_code=400, detail="name and symbol required when project_id is not set")
        name, symbol = body.name, body.symbol
        description = body.description or ""
        image = body.image or ""
        external_url = body.external_url or ""
        out_path = body.output_path or str(Path(state.STATE_FILE).parent / "metadata.json")
    try:
        path = write_metadata_json(out_path, name=name, symbol=symbol, description=description, image=image, external_url=external_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    result: dict[str, Any] = {"output_path": str(path)}
    if body.upload_to_ipfs:
        try:
            token_uri = upload_to_ipfs(path)
            result["token_uri"] = token_uri
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"IPFS upload failed: {e}")
    return result


@app.get("/health")
def health() -> dict[str, str]:
    """Health check for load balancers."""
    return {"status": "ok"}