"""
Token metadata: off-chain JSON (name, icon, description, etc.) and optional Metaplex on-chain metadata.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Metaplex-style off-chain metadata (what lives at token_uri)
# https://docs.metaplex.com/programs/token-metadata/accounts#metadata-json-structure


def build_metadata_json(
    name: str,
    symbol: str,
    description: str = "",
    image: str = "",
    external_url: str = "",
    attributes: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build the standard metadata JSON for a token (Metaplex / Solana ecosystem).
    Wallets and explorers fetch this from token_uri to show name, icon, description, etc.
    """
    data: dict[str, Any] = {
        "name": name,
        "symbol": symbol,
        "description": description or "",
        "image": image or "",
        "external_url": external_url or "",
    }
    if attributes:
        data["attributes"] = attributes
    if extra:
        data.update(extra)
    return data


def write_metadata_json(
    output_path: str | Path,
    name: str,
    symbol: str,
    description: str = "",
    image: str = "",
    external_url: str = "",
    attributes: list[dict[str, Any]] | None = None,
    **extra: Any,
) -> Path:
    """
    Write metadata JSON to a file. Upload this to IPFS/Arweave and use the URL as token_uri.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_metadata_json(
        name=name,
        symbol=symbol,
        description=description,
        image=image,
        external_url=external_url,
        attributes=attributes,
        extra=extra if extra else None,
    )
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path
