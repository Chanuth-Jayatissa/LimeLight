"""
Create SPL token mints for projects and mint project tokens to buyers on Solana Devnet.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from spl.token.client import Token
from spl.token.constants import TOKEN_PROGRAM_ID

# Token decimals for project mints (1 token = 10^DECIMALS raw units)
DECIMALS = 6

# Default Devnet RPC; override with env SOLANA_RPC_URL
DEFAULT_RPC = "https://api.devnet.solana.com"
# Always use this for Phantom / app flows so sells never go to mainnet by mistake
DEVNET_RPC = "https://api.devnet.solana.com"


def get_rpc_url() -> str:
    return os.environ.get("SOLANA_RPC_URL", DEFAULT_RPC)


def get_client() -> Client:
    return Client(get_rpc_url())


def get_client_devnet() -> Client:
    """Always return a client connected to Solana Devnet. Use for Phantom sign flow so transactions never go to mainnet."""
    return Client(DEVNET_RPC)


def load_keypair(path: str) -> Keypair:
    """Load keypair from JSON file (Solana CLI format: array of 64 bytes)."""
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"Keypair file not found: {path}")
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    return Keypair.from_bytes(bytes(data))


def load_keypair_from_base64(keypair_base64: str) -> Keypair:
    """Load keypair from base64-encoded secret (64 bytes). For API use."""
    import base64
    decoded = base64.standard_b64decode(keypair_base64)
    if len(decoded) != 64:
        raise ValueError("Keypair must be 64 bytes when decoded")
    return Keypair.from_bytes(decoded)


def get_platform_keypair() -> Keypair | None:
    """
    Load the platform keypair from env. Used to create mints and sign buy transfers
    so users don't need to send keypairs. Set one of:
    - PLATFORM_KEYPAIR_BASE64: base64-encoded 64-byte secret
    - PLATFORM_KEYPAIR_PATH: path to keypair JSON file (e.g. id.json)
    """
    import os
    b64 = os.environ.get("PLATFORM_KEYPAIR_BASE64", "").strip()
    if b64:
        try:
            return load_keypair_from_base64(b64)
        except Exception:
            return None
    path = os.environ.get("PLATFORM_KEYPAIR_PATH", "").strip()
    if path:
        try:
            return load_keypair(path)
        except Exception:
            return None
    return None


def create_mint_for_project(
    conn: Client,
    payer: Keypair,
    decimals: int = DECIMALS,
    token_name: str | None = None,
    token_symbol: str | None = None,
    token_uri: str | None = None,
    initial_supply: int = 0,
    vault_owner_pubkey: Pubkey | None = None,
) -> str:
    """
    Create a new SPL token mint on Devnet. Payer is the mint authority and pays for creation.
    If token_name, token_symbol, and token_uri are provided, also creates Metaplex metadata.
    If initial_supply > 0, mints that many tokens to the vault:
      - If vault_owner_pubkey is set, mints to that wallet's ATA (payer still pays for ATA if created).
      - If vault_owner_pubkey is None, mints to the payer's ATA (vault = platform wallet).

    Returns:
        Mint address (public key string).
    """
    token = Token.create_mint(
        conn,
        payer=payer,
        mint_authority=payer.pubkey(),
        decimals=decimals,
        program_id=TOKEN_PROGRAM_ID,
        freeze_authority=None,
        skip_confirmation=False,
    )
    mint_address = str(token.pubkey)
    if token_name and token_symbol and token_uri:
        create_metadata_for_mint(
            conn,
            mint_address=mint_address,
            payer=payer,
            name=token_name,
            symbol=token_symbol,
            uri=token_uri,
        )
    if initial_supply > 0:
        mint_pubkey = Pubkey.from_string(mint_address)
        vault_owner = vault_owner_pubkey if vault_owner_pubkey is not None else payer.pubkey()
        vault_ata = get_or_create_ata(conn, mint_pubkey, vault_owner, payer)
        raw_supply = tokens_to_raw(initial_supply, decimals)
        token.mint_to(
            dest=vault_ata,
            mint_authority=payer,
            amount=raw_supply,
        )
    return mint_address


def create_metadata_for_mint(
    conn: Client,
    mint_address: str,
    payer: Keypair,
    name: str,
    symbol: str,
    uri: str,
    seller_fee_basis_points: int = 0,
) -> str:
    """
    Create Metaplex metadata account for an existing mint. Wallets will show
    name, symbol, and fetch icon/description from the JSON at uri.
    """
    from solders.message import Message
    from solders.transaction import Transaction

    from .metaplex_metadata import create_metadata_account_v3_instruction

    mint_pubkey = Pubkey.from_string(mint_address)
    ix = create_metadata_account_v3_instruction(
        mint=mint_pubkey,
        mint_authority=payer.pubkey(),
        payer=payer.pubkey(),
        update_authority=payer.pubkey(),
        name=name,
        symbol=symbol,
        uri=uri,
        seller_fee_basis_points=seller_fee_basis_points,
        creator_pubkey=payer.pubkey(),
    )
    blockhash_resp = conn.get_latest_blockhash()
    blockhash = blockhash_resp.value.blockhash
    msg = Message.new_with_blockhash([ix], payer.pubkey(), blockhash)
    tx = Transaction([payer], msg, blockhash)
    resp = conn.send_transaction(tx)
    return str(resp.value)


def get_or_create_ata(
    conn: Client,
    mint_pubkey: Pubkey,
    owner_pubkey: Pubkey,
    payer: Keypair,
    token_program_id: Pubkey = TOKEN_PROGRAM_ID,
) -> Pubkey:
    """Get associated token account address; create the account if it doesn't exist."""
    from spl.token.instructions import get_associated_token_address

    ata = get_associated_token_address(owner_pubkey, mint_pubkey, token_program_id)
    info = conn.get_account_info(ata)
    if info.value is None:
        # Create ATA using Token client (needs a Token instance with same mint)
        token_client = Token(conn, mint_pubkey, token_program_id, payer)
        token_client.create_associated_token_account(
            owner=owner_pubkey,
            skip_confirmation=False,
        )
    return ata


def tokens_to_raw(amount: int, decimals: int = DECIMALS) -> int:
    """Convert whole tokens to raw SPL amount (amount * 10^decimals)."""
    return amount * (10**decimals)


def mint_tokens_to_buyer(
    conn: Client,
    mint_address: str,
    buyer_pubkey: Pubkey,
    amount: int,
    mint_authority: Keypair,
    payer: Keypair,
    decimals: int = DECIMALS,
    vault_owner_pubkey: Pubkey | None = None,
    vault_signer_keypair: Keypair | None = None,
) -> str:
    """
    Transfer project tokens from the vault to the buyer's wallet.
    Fixed supply: no minting on buy; only transfers from pre-minted vault.
    Creates buyer's ATA if needed.
    If vault_owner_pubkey is set, transfer from that wallet's ATA (vault_signer_keypair must sign).
    If not set, vault = payer's ATA (platform wallet).

    Returns:
        Signature of the transaction.
    """
    raw_amount = tokens_to_raw(amount, decimals)
    mint_pubkey = Pubkey.from_string(mint_address)
    token = Token(conn, mint_pubkey, TOKEN_PROGRAM_ID, payer)
    dest_ata = get_or_create_ata(conn, mint_pubkey, buyer_pubkey, payer)
    vault_owner = vault_owner_pubkey if vault_owner_pubkey is not None else payer.pubkey()
    vault_signer = vault_signer_keypair if vault_signer_keypair is not None else payer
    vault_ata = get_or_create_ata(conn, mint_pubkey, vault_owner, payer)
    try:
        balance_resp = conn.get_token_account_balance(vault_ata)
        vault_balance = int(balance_resp.value.amount) if balance_resp.value else 0
    except Exception:
        vault_balance = 0
    if vault_balance < raw_amount:
        raise RuntimeError(
            f"Insufficient vault balance: have {vault_balance} raw ({vault_balance / (10**decimals):.0f} tokens), "
            f"need {raw_amount} raw ({amount} tokens). Fixed supply; no minting on buy."
        )
    resp = token.transfer(
        source=vault_ata,
        dest=dest_ata,
        owner=vault_signer,
        amount=raw_amount,
    )
    return str(resp.value)


def transfer_tokens_to_vault(
    conn: Client,
    mint_address: str,
    seller_pubkey: Pubkey,
    amount: int,
    seller_keypair: Keypair,
    payer: Keypair,
    vault_owner_pubkey: Pubkey,
    decimals: int = DECIMALS,
) -> str:
    """
    Transfer tokens from seller's ATA to the project vault (for sell-back).
    Seller must sign (seller_keypair is owner of source ATA).
    """
    from spl.token.instructions import get_associated_token_address

    raw_amount = tokens_to_raw(amount, decimals)
    mint_pubkey = Pubkey.from_string(mint_address)
    token = Token(conn, mint_pubkey, TOKEN_PROGRAM_ID, payer)
    seller_ata = get_associated_token_address(seller_pubkey, mint_pubkey, TOKEN_PROGRAM_ID)
    vault_ata = get_associated_token_address(vault_owner_pubkey, mint_pubkey, TOKEN_PROGRAM_ID)
    resp = token.transfer(
        source=seller_ata,
        dest=vault_ata,
        owner=seller_keypair,
        amount=raw_amount,
    )
    return str(resp.value)


def build_unsigned_sell_transaction(
    conn: Client,
    mint_address: str,
    seller_pubkey: Pubkey,
    amount: int,
    vault_owner_pubkey: Pubkey,
    decimals: int = DECIMALS,
) -> bytes:
    """
    Build an unsigned SPL transfer transaction (seller -> vault) for a wallet (e.g. Phantom) to sign.
    Returns serialized transaction bytes (base64-encode for sending to browser).
    """
    from solders.message import Message
    from solders.transaction import Transaction
    from spl.token.instructions import (
        get_associated_token_address,
        transfer_checked,
        TransferCheckedParams,
    )

    raw_amount = tokens_to_raw(amount, decimals)
    mint_pubkey = Pubkey.from_string(mint_address)
    seller_ata = get_associated_token_address(seller_pubkey, mint_pubkey, TOKEN_PROGRAM_ID)
    vault_ata = get_associated_token_address(vault_owner_pubkey, mint_pubkey, TOKEN_PROGRAM_ID)

    ix = transfer_checked(
        TransferCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            source=seller_ata,
            mint=mint_pubkey,
            dest=vault_ata,
            owner=seller_pubkey,
            amount=raw_amount,
            decimals=decimals,
        )
    )
    blockhash_resp = conn.get_latest_blockhash()
    blockhash = blockhash_resp.value.blockhash
    msg = Message.new_with_blockhash([ix], seller_pubkey, blockhash)
    tx = Transaction.new_unsigned(msg)
    return bytes(tx)


def submit_signed_transaction(conn: Client, signed_tx_bytes: bytes) -> str:
    """Submit a signed transaction (e.g. from Phantom) and return the signature."""
    resp = conn.send_raw_transaction(signed_tx_bytes)
    return str(resp.value)
