"""
Create Metaplex Token Metadata on-chain (name, symbol, uri) so wallets show token name and icon.
"""
from __future__ import annotations

import struct
from typing import Optional

from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey
from solders.sysvar import RENT
from solders.system_program import ID as SYS_PROGRAM_ID

# Metaplex Token Metadata program (same on mainnet and devnet)
TOKEN_METADATA_PROGRAM_ID = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")


def _borsh_string(s: str) -> bytes:
    """Encode string as Borsh: 4-byte LE length + UTF-8 bytes."""
    b = s.encode("utf-8")
    return struct.pack("<I", len(b)) + b


def _create_metadata_instruction_data(
    name: str,
    symbol: str,
    uri: str,
    seller_fee_basis_points: int = 0,
    creators: Optional[list[tuple[bytes, bool, int]]] = None,
) -> bytes:
    """
    Build CreateMetadataAccountV3 instruction data (Borsh).
    creators: list of (address_32_bytes, verified, share).
    """
    # Instruction discriminator for CreateMetadataAccountV3
    data = bytearray([33])
    # Data struct
    data += _borsh_string(name)
    data += _borsh_string(symbol)
    data += _borsh_string(uri)
    data += struct.pack("<H", min(65535, max(0, seller_fee_basis_points)))
    # creators: Option<Vec<Creator>>
    if creators:
        data += bytes([1])  # Some
        data += struct.pack("<I", len(creators))
        for addr_32, verified, share in creators:
            data += addr_32  # 32 bytes
            data += bytes([1 if verified else 0])
            data += struct.pack("<B", min(255, share))
    else:
        data += bytes([0])  # None
    # collection: Option - None
    data += bytes([0])
    # uses: Option - None
    data += bytes([0])
    # is_mutable: bool
    data += bytes([1])
    # collection_details: Option - None
    data += bytes([0])
    return bytes(data)


def get_metadata_pda(mint: Pubkey) -> Pubkey:
    """Derive the metadata account PDA for a mint."""
    pda, _ = Pubkey.find_program_address(
        seeds=[b"metadata", bytes(TOKEN_METADATA_PROGRAM_ID), bytes(mint)],
        program_id=TOKEN_METADATA_PROGRAM_ID,
    )
    return pda


def create_metadata_account_v3_instruction(
    mint: Pubkey,
    mint_authority: Pubkey,
    payer: Pubkey,
    update_authority: Pubkey,
    name: str,
    symbol: str,
    uri: str,
    seller_fee_basis_points: int = 0,
    creator_pubkey: Optional[Pubkey] = None,
) -> Instruction:
    """
    Build the CreateMetadataAccountV3 instruction. After this, wallets can show
    token name, symbol, and fetch icon/description from the JSON at uri.
    """
    metadata_pda = get_metadata_pda(mint)
    creators = None
    if creator_pubkey is not None:
        creators = [(bytes(creator_pubkey), False, 100)]
    ix_data = _create_metadata_instruction_data(
        name=name,
        symbol=symbol,
        uri=uri,
        seller_fee_basis_points=seller_fee_basis_points,
        creators=creators,
    )
    accounts = [
        AccountMeta(pubkey=metadata_pda, is_signer=False, is_writable=True),
        AccountMeta(pubkey=mint, is_signer=False, is_writable=False),
        AccountMeta(pubkey=mint_authority, is_signer=True, is_writable=False),
        AccountMeta(pubkey=payer, is_signer=True, is_writable=True),
        AccountMeta(pubkey=update_authority, is_signer=False, is_writable=False),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
    ]
    return Instruction(
        program_id=TOKEN_METADATA_PROGRAM_ID,
        data=ix_data,
        accounts=accounts,
    )
