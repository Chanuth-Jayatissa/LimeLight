"""
Derive Solana addresses for projects (PDAs) so users can look them up on-chain.

Uses a configurable program ID (env STARTUP_CLI_PROGRAM_ID or default placeholder).
When you deploy your program, set the same program ID so these addresses match.
"""
from __future__ import annotations

import os
from typing import Tuple

from solders.pubkey import Pubkey

# Default: placeholder. Set STARTUP_CLI_PROGRAM_ID to your deployed program ID.
_DEFAULT_PROGRAM_ID = "11111111111111111111111111111111"


def _program_id() -> Pubkey:
    return Pubkey.from_string(
        os.environ.get("STARTUP_CLI_PROGRAM_ID", _DEFAULT_PROGRAM_ID)
    )


def get_project_address(project_id: int) -> str:
    """Derive the project account PDA for a given project ID."""
    seeds = [b"project", project_id.to_bytes(4, "little")]
    pda, _ = Pubkey.find_program_address(seeds=seeds, program_id=_program_id())
    return str(pda)


def get_treasury_address(project_id: int) -> str:
    """Derive the treasury account PDA for a given project ID."""
    seeds = [b"treasury", project_id.to_bytes(4, "little")]
    pda, _ = Pubkey.find_program_address(seeds=seeds, program_id=_program_id())
    return str(pda)


def get_project_addresses(project_id: int) -> Tuple[str, str]:
    """Return (project_account_address, treasury_address)."""
    return (get_project_address(project_id), get_treasury_address(project_id))
