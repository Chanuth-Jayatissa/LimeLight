"""
Upload files to IPFS automatically (Pinata or local node).
Set PINATA_JWT in env for Pinata, or run a local IPFS node for local upload.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

PINATA_PIN_URL = "https://api.pinata.cloud/pinning/pinFileToIPFS"
PINATA_GATEWAY = "https://gateway.pinata.cloud/ipfs"
DEVNET_EXPLORER = "https://explorer.solana.com"


def upload_to_ipfs(file_path: str | Path) -> str:
    """
    Upload a file to IPFS and return the public gateway URL.
    Uses Pinata if PINATA_JWT is set, else tries local IPFS node.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # 1) Try Pinata (no local node needed)
    jwt = (os.environ.get("PINATA_JWT") or "").strip()
    if jwt:
        return _upload_via_pinata(path, jwt)

    # 2) Try local IPFS node
    try:
        return _upload_via_local_ipfs(path)
    except Exception:
        pass

    raise RuntimeError(
        "IPFS upload failed. Set PINATA_JWT in env (get a free JWT at https://app.pinata.cloud), "
        "or run a local IPFS node (ipfs daemon)."
    )


def _upload_via_pinata(path: Path, jwt: str) -> str:
    """Pin file to IPFS via Pinata API; return gateway URL."""
    import httpx

    headers = {"Authorization": f"Bearer {jwt}"}
    with open(path, "rb") as f:
        files = {"file": (path.name, f, "application/octet-stream")}
        resp = httpx.post(PINATA_PIN_URL, headers=headers, files=files, timeout=60.0)
    resp.raise_for_status()
    data = resp.json()
    ipfs_hash = data.get("IpfsHash") or data.get("cid")
    if not ipfs_hash:
        raise RuntimeError(f"Pinata response missing hash: {data}")
    return f"{PINATA_GATEWAY}/{ipfs_hash}"


def _upload_via_local_ipfs(path: Path) -> str:
    """Add file via local IPFS node (ipfs daemon); return gateway URL."""
    try:
        import ipfshttpclient
    except ImportError:
        raise RuntimeError(
            "Local IPFS requires: pip install ipfshttpclient. Or use Pinata: set PINATA_JWT."
        ) from None
    client = ipfshttpclient.connect()
    result = client.add(str(path))
    if isinstance(result, dict):
        cid = result.get("Hash") or result.get("hash")
    else:
        cid = getattr(result, "Hash", None) or str(result)
    if not cid:
        raise RuntimeError(f"Local IPFS add returned no hash: {result}")
    return f"https://ipfs.io/ipfs/{cid}"


def get_devnet_mint_url(mint_address: str) -> str:
    """Return Solana Explorer Devnet URL for a mint address."""
    return f"{DEVNET_EXPLORER}/address/{mint_address}?cluster=devnet"
