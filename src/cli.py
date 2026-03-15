"""
CLI for launching tokenized startup projects on Solana Devnet.

Supports bonding curve pricing (linear and exponential).
"""
from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .addresses import get_project_addresses
from .bonding_curve import (
    DEFAULT_CURVE_TYPE,
    DEFAULT_INITIAL_PRICE,
    CurveType,
    calculate_purchase_cost,
    derive_curve_params,
    get_current_price,
)
from .solana_mint import (
    create_mint_for_project,
    get_client,
    load_keypair,
    mint_tokens_to_buyer,
    transfer_tokens_to_vault,
)
from .state import (
    create_project as create_project_state,
    delete_project,
    get_project,
    list_projects,
    set_project_mint,
    set_project_token_metadata,
    update_project_tokens_and_treasury,
)
from .ipfs_upload import get_devnet_mint_url, upload_to_ipfs
from .token_metadata import write_metadata_json

app = typer.Typer(
    name="startup-cli",
    help="Launch tokenized startup projects on Solana Devnet. Investors buy tokens; price follows a bonding curve.",
)
console = Console()


@app.command()
def create_project(
    name: str = typer.Option(..., "--name", "-n", help="Project name"),
    description: str = typer.Option(..., "--description", "-d", help="Short description"),
    github: str = typer.Option(..., "--github", "-g", help="GitHub URL"),
    supply: int = typer.Option(100_000, "--supply", "-s", help="Total token supply (default 100,000; fixed limited supply for bonding curve)"),
    initial_price: Optional[float] = typer.Option(None, "--initial-price", "-p", help="Initial token price (SOL). Omit for default 0.01."),
    curve_type: Optional[CurveType] = typer.Option(
        None,
        "--curve-type",
        "-c",
        help="Bonding curve: linear or exponential. Omit for default 'linear'.",
    ),
    price_increment: Optional[float] = typer.Option(
        None,
        "--price-increment",
        help="Price growth per token (linear curve only, e.g. 0.00001)",
    ),
    k: Optional[float] = typer.Option(
        None,
        "--k",
        help="Growth constant for exponential curve (e.g. 0.0005)",
    ),
    target_end_price: Optional[float] = typer.Option(
        None,
        "--target-end-price",
        help="Target price when supply is fully sold; used to derive --price-increment (linear) or --k (exponential) if omitted",
    ),
    price_multiplier: Optional[float] = typer.Option(
        None,
        "--price-multiplier",
        help="End price = initial_price × this (e.g. 10 => 10x at end). Used to derive curve params if omitted. Default 10 if none set.",
    ),
    token_name: Optional[str] = typer.Option(None, "--token-name", help="Token display name (for mint metadata)"),
    token_symbol: Optional[str] = typer.Option(None, "--token-symbol", help="Token symbol (e.g. DRAFT)"),
    token_uri: Optional[str] = typer.Option(None, "--token-uri", help="URL to token metadata JSON (name, icon, description)"),
    token_description: Optional[str] = typer.Option(None, "--token-description", help="Token description (for metadata JSON)"),
    token_image: Optional[str] = typer.Option(None, "--token-image", help="URL to token icon image"),
    token_external_url: Optional[str] = typer.Option(None, "--token-external-url", help="Project/external link for token"),
    upload_to_ipfs_flag: bool = typer.Option(
        False,
        "--upload-to-ipfs",
        help="Generate token metadata JSON and upload to IPFS; set token_uri on project (requires PINATA_JWT)",
    ),
) -> None:
    """Create a new tokenized startup project. initial_price, curve_type, price_increment, and k are optional (defaults: 0.01 SOL, linear, 10x at full supply). Use --upload-to-ipfs to auto-upload token metadata."""
    initial_price_resolved = initial_price if initial_price is not None else DEFAULT_INITIAL_PRICE
    curve_type_resolved: CurveType = curve_type if curve_type is not None else DEFAULT_CURVE_TYPE
    if (curve_type_resolved == "linear" and price_increment is None) or (curve_type_resolved == "exponential" and k is None):
        end_price = target_end_price
        mult = price_multiplier
        if end_price is None and mult is None:
            mult = 10.0
        try:
            inc, k_derived = derive_curve_params(
                curve_type_resolved, initial_price_resolved, float(supply),
                end_price=end_price, price_multiplier=mult,
            )
            if inc is not None:
                price_increment = inc
            if k_derived is not None:
                k = k_derived
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
    if curve_type_resolved == "linear" and price_increment is None:
        typer.echo("Error: set --price-increment or --target-end-price or --price-multiplier for linear curve.", err=True)
        raise typer.Exit(1)
    if curve_type_resolved == "exponential" and k is None:
        typer.echo("Error: set --k or --target-end-price or --price-multiplier for exponential curve.", err=True)
        raise typer.Exit(1)

    project = create_project_state(
        name=name,
        description=description,
        github=github,
        supply=supply,
        initial_price=initial_price_resolved,
        curve_type=curve_type_resolved,
        price_increment=price_increment,
        k=k,
    )
    pid = project["id"]
    t_name = token_name or name
    t_symbol = token_symbol or "".join(c[0].upper() for c in name.split() if c)[:10] or "TKN"
    t_description = token_description or description or ""
    t_image = token_image or ""
    t_external_url = token_external_url or github or ""
    if any([token_name, token_symbol, token_uri, token_description, token_image, token_external_url]) or upload_to_ipfs_flag:
        set_project_token_metadata(
            pid,
            token_name=t_name,
            token_symbol=t_symbol,
            token_uri=token_uri,
            token_description=t_description,
            token_image=t_image,
            token_external_url=t_external_url,
        )
    if upload_to_ipfs_flag:
        if token_uri:
            console.print("[yellow]--upload-to-ipfs ignored because --token-uri was provided.[/yellow]")
        else:
            console.print("Uploading token metadata to IPFS...")
            try:
                meta_path = write_metadata_json(
                    f"data/metadata_{pid}.json",
                    name=t_name,
                    symbol=t_symbol,
                    description=t_description,
                    image=t_image,
                    external_url=t_external_url,
                )
                token_uri = upload_to_ipfs(meta_path)
                set_project_token_metadata(pid, token_uri=token_uri)
                console.print(f"[green]Uploaded. Token URI saved to project:[/green] [cyan]{token_uri}[/cyan]")
            except Exception as e:
                console.print(f"[red]IPFS upload failed: {e}[/red]")
                raise typer.Exit(1)
    project_addr, treasury_addr = get_project_addresses(pid)
    devnet_explorer = "https://explorer.solana.com"
    console.print(f"[green]Project created.[/green] ID: [bold]{pid}[/bold]")
    console.print(f"  Name: {project['name']}")
    console.print(f"  Curve: {project['curve_type']}")
    console.print(f"  Supply: {project['supply']} tokens, initial price: {project['initial_price']} SOL")
    console.print()
    console.print("[bold]Blockchain addresses (Devnet):[/bold]")
    console.print(f"  Project account:  [cyan]{project_addr}[/cyan]")
    console.print(f"  Treasury account: [cyan]{treasury_addr}[/cyan]")
    console.print(f"  View on Explorer: [link={devnet_explorer}/address/{project_addr}?cluster=devnet]{devnet_explorer}/address/{project_addr}?cluster=devnet[/link]")
    if upload_to_ipfs_flag and token_uri:
        console.print()
        console.print("Next: create mint with the saved token_uri:")
        console.print(f"  startup-cli create-mint --project-id {pid} --keypair <path> --token-name \"{t_name}\" --token-symbol {t_symbol} --token-uri \"{token_uri}\"")


@app.command("delete-project")
def delete_project_cmd(
    project_id: int = typer.Option(..., "--project-id", "-i", help="Project ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a project from local state. On-chain mint/accounts are not removed."""
    project = get_project(project_id)
    if not project:
        console.print(f"[red]Project with ID {project_id} not found.[/red]")
        raise typer.Exit(1)
    if project.get("mint_address"):
        console.print(f"[yellow]This project has a mint on-chain ({project['mint_address']}). Deleting only removes local state; the mint and any token accounts remain on Devnet.[/yellow]")
    if not force and not typer.confirm(f"Delete project '{project['name']}' (ID {project_id})?"):
        console.print("Cancelled.")
        return
    if delete_project(project_id):
        console.print(f"[green]Project {project_id} deleted.[/green]")
    else:
        console.print(f"[red]Failed to delete project {project_id}.[/red]")
        raise typer.Exit(1)


@app.command()
def create_mint(
    project_id: int = typer.Option(..., "--project-id", "-i", help="Project ID"),
    keypair: str = typer.Option(
        ...,
        "--keypair",
        "-k",
        help="Path to payer/mint-authority keypair JSON (e.g. ~/.config/solana/id.json)",
    ),
    token_name: Optional[str] = typer.Option(None, "--token-name", help="Token name (overrides project; required for metadata)"),
    token_symbol: Optional[str] = typer.Option(None, "--token-symbol", help="Token symbol (overrides project)"),
    token_uri: Optional[str] = typer.Option(None, "--token-uri", help="URL to metadata JSON with icon, description (overrides project)"),
) -> None:
    """Create an SPL token mint on Devnet. Pre-mints the full project supply (fixed 100k) to the vault; buys transfer from vault (no minting on buy)."""
    project = get_project(project_id)
    if not project:
        console.print(f"[red]Project with ID {project_id} not found.[/red]")
        raise typer.Exit(1)
    if project.get("mint_address"):
        console.print(f"[yellow]Project already has a mint: {project['mint_address']}[/yellow]")
        if not typer.confirm("Continue anyway (this will create a new mint)?"):
            return
    try:
        kp = load_keypair(keypair)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    # Use CLI args or fall back to project token metadata
    name = token_name or project.get("token_name")
    symbol = token_symbol or project.get("token_symbol")
    uri = token_uri or project.get("token_uri")
    if name or symbol or uri:
        console.print(f"Token metadata: name={name or '(none)'}, symbol={symbol or '(none)'}, uri={uri or '(none)'}")
        if not all([name, symbol, uri]):
            console.print("[yellow]Provide all of --token-name, --token-symbol, --token-uri to attach on-chain metadata (wallets show name/icon).[/yellow]")
    supply = project.get("supply", 100_000) or 100_000
    console.print(f"Pre-minting fixed supply: {supply} tokens (limited supply; bonding curve applies; no minting on buy).")
    console.print("Creating SPL token mint on Devnet...")
    conn = get_client()
    try:
        mint_address = create_mint_for_project(
            conn, kp,
            token_name=name,
            token_symbol=symbol,
            token_uri=uri,
            initial_supply=supply,
        )
    except Exception as e:
        console.print(f"[red]Failed to create mint: {e}[/red]")
        raise typer.Exit(1)
    set_project_mint(project_id, mint_address, vault_owner=str(kp.pubkey()))
    if name or symbol or uri:
        set_project_token_metadata(project_id, token_name=name, token_symbol=symbol, token_uri=uri)
    explorer_url = get_devnet_mint_url(mint_address)
    console.print(f"[green]Mint created on Devnet.[/green]")
    console.print(f"  Mint address: [cyan]{mint_address}[/cyan]")
    console.print(f"  [bold]View mint on Devnet:[/bold] [link={explorer_url}]{explorer_url}[/link]")
    if name and symbol and uri:
        console.print("  Metadata attached: wallets will show name, symbol, and fetch icon from token_uri.")
    console.print(f"  Supply: [green]{supply}[/green] tokens pre-minted to vault (fixed supply); buys transfer from vault; bonding curve sets price.")
    console.print("Investors can now buy these project tokens with buy-tokens (pay SOL, receive tokens).")


@app.command()
def buy_tokens(
    project_id: int = typer.Option(..., "--project-id", "-i", help="Project ID"),
    amount: int = typer.Option(..., "--amount", "-a", help="Number of project tokens to buy"),
    buyer: Optional[str] = typer.Option(
        None,
        "--buyer",
        "-b",
        help="Buyer wallet address (SOL pubkey). Required if project has a mint (on-chain purchase).",
    ),
    keypair: Optional[str] = typer.Option(
        None,
        "--keypair",
        "-k",
        help="Path to mint-authority keypair (for on-chain mint). Required if project has a mint.",
    ),
) -> None:
    """Buy project tokens: pay SOL (price from bonding curve), receive the project's minted SPL tokens."""
    project = get_project(project_id)
    if not project:
        console.print(f"[red]Project with ID {project_id} not found.[/red]")
        raise typer.Exit(1)

    tokens_sold = project["tokens_sold"]
    supply = project["supply"]
    if tokens_sold + amount > supply:
        console.print(f"[red]Not enough tokens. Remaining: {supply - tokens_sold}, requested: {amount}.[/red]")
        raise typer.Exit(1)

    try:
        cost, price_after = calculate_purchase_cost(
            curve_type=project["curve_type"],
            base_price=project["initial_price"],
            tokens_sold=tokens_sold,
            amount=amount,
            price_increment=project.get("price_increment"),
            k=project.get("k"),
        )
    except ValueError as e:
        console.print(f"[red]Pricing error: {e}[/red]")
        raise typer.Exit(1)

    current_price = get_current_price(
        curve_type=project["curve_type"],
        base_price=project["initial_price"],
        tokens_sold=tokens_sold,
        price_increment=project.get("price_increment"),
        k=project.get("k"),
    )

    # Show price calculations
    table = Table(title="Purchase summary")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Project", f"{project['name']} (ID {project_id})")
    table.add_row("Current token price", f"{current_price:.8f} SOL")
    table.add_row("Tokens to buy", str(amount))
    table.add_row("Total cost (MVP approx)", f"{cost:.8f} SOL")
    table.add_row("Price after purchase", f"{price_after:.8f} SOL")
    table.add_row("Tokens remaining (before)", f"{supply - tokens_sold}")
    table.add_row("Tokens remaining (after)", f"{supply - tokens_sold - amount}")
    table.add_row("Treasury balance (before)", f"{project['treasury_balance']:.8f} SOL")
    table.add_row("Treasury balance (after)", f"{project['treasury_balance'] + cost:.8f} SOL")
    mint_addr = project.get("mint_address")
    if mint_addr:
        table.add_row("Project token mint", mint_addr)
    console.print(table)
    project_addr, treasury_addr = get_project_addresses(project_id)
    console.print("[bold]Blockchain addresses (Devnet):[/bold]")
    console.print(f"  Treasury: [cyan]{treasury_addr}[/cyan]")
    console.print(f"  Explorer: https://explorer.solana.com/address/{treasury_addr}?cluster=devnet")

    # On-chain: mint project tokens to buyer
    if mint_addr:
        if not buyer or not keypair:
            console.print(
                "[red]This project has a mint. Provide --buyer (wallet pubkey) and --keypair (mint authority) to mint tokens on-chain.[/red]"
            )
            raise typer.Exit(1)
        if not typer.confirm("Confirm purchase? (SOL cost is simulated; tokens will be minted to buyer wallet.)"):
            console.print("Purchase cancelled.")
            return
        try:
            from solders.pubkey import Pubkey
            kp = load_keypair(keypair)
            buyer_pubkey = Pubkey.from_string(buyer)
            conn = get_client()
            sig = mint_tokens_to_buyer(conn, mint_addr, buyer_pubkey, amount, kp, kp)
            update_project_tokens_and_treasury(project_id, amount, cost)
            console.print(f"[green]Minted {amount} project tokens to {buyer}. Tx: {sig}[/green]")
        except Exception as e:
            console.print(f"[red]Mint failed: {e}[/red]")
            raise typer.Exit(1)
    else:
        if not typer.confirm("Confirm purchase? (No project mint yet; only local state will be updated.)"):
            console.print("Purchase cancelled.")
            return
        update_project_tokens_and_treasury(project_id, amount, cost)
        console.print(f"[green]Purchased {amount} tokens for {cost:.8f} SOL (local state only).[/green]")
        console.print("[dim]Run create-mint for this project, then buy-tokens with --buyer and --keypair to mint on-chain.[/dim]")


@app.command("sell-tokens")
def sell_tokens(
    project_id: int = typer.Option(..., "--project-id", "-i", help="Project ID"),
    amount: int = typer.Option(..., "--amount", "-a", help="Number of project tokens to sell back"),
    keypair: str = typer.Option(..., "--keypair", "-k", help="Path to your wallet keypair (the one holding the tokens, e.g. Phantom export)"),
    vault_authority: Optional[str] = typer.Option(
        None,
        "--vault-authority",
        help="Vault owner pubkey (where tokens go). Default: project's stored vault_owner from create-mint.",
    ),
) -> None:
    """Sell project tokens back: send tokens from your wallet to the project vault; local state and SOL payout are updated. Run with the keypair of the wallet that holds the tokens (e.g. Phantom exported key)."""
    from solders.pubkey import Pubkey

    project = get_project(project_id)
    if not project:
        console.print(f"[red]Project with ID {project_id} not found.[/red]")
        raise typer.Exit(1)

    mint_addr = project.get("mint_address")
    if not mint_addr:
        console.print("[red]This project has no mint. Only projects with an on-chain mint support selling.[/red]")
        raise typer.Exit(1)

    vault_owner = vault_authority or project.get("vault_owner")
    if not vault_owner:
        console.print(
            "[red]Project has no vault_owner. Pass --vault-authority <pubkey> (the wallet that ran create-mint).[/red]"
        )
        raise typer.Exit(1)

    tokens_sold = project["tokens_sold"]
    if amount <= 0:
        console.print("[red]Amount must be positive.[/red]")
        raise typer.Exit(1)
    if tokens_sold < amount:
        console.print(f"[red]Cannot sell more than was bought. tokens_sold={tokens_sold}, requested={amount}.[/red]")
        raise typer.Exit(1)

    current_price = get_current_price(
        curve_type=project["curve_type"],
        base_price=project["initial_price"],
        tokens_sold=tokens_sold,
        price_increment=project.get("price_increment"),
        k=project.get("k"),
    )
    sell_value = current_price * amount

    table = Table(title="Sell summary")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Project", f"{project['name']} (ID {project_id})")
    table.add_row("Current token price", f"{current_price:.8f} SOL")
    table.add_row("Tokens to sell", str(amount))
    table.add_row("You receive (approx)", f"{sell_value:.8f} SOL")
    table.add_row("Treasury (before)", f"{project['treasury_balance']:.8f} SOL")
    table.add_row("Treasury (after)", f"{project['treasury_balance'] - sell_value:.8f} SOL")
    console.print(table)
    console.print("[dim]Note: This CLI only transfers tokens to the vault and updates local state. The project owner must send you SOL separately (or use an on-chain treasury in future).[/dim]")

    if not typer.confirm("Confirm sell? Tokens will be sent from your wallet to the project vault."):
        console.print("Sell cancelled.")
        return

    try:
        kp = load_keypair(keypair)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    conn = get_client()
    try:
        sig = transfer_tokens_to_vault(
            conn,
            mint_address=mint_addr,
            seller_pubkey=kp.pubkey(),
            amount=amount,
            seller_keypair=kp,
            payer=kp,
            vault_owner_pubkey=Pubkey.from_string(vault_owner),
        )
        update_project_tokens_and_treasury(project_id, -amount, -sell_value)
        console.print(f"[green]Sold {amount} tokens. Tx: {sig}[/green]")
        console.print(f"You are owed ~{sell_value:.8f} SOL by the project; the project owner should send it to your wallet.")
    except Exception as e:
        console.print(f"[red]Sell failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("generate-token-metadata")
def generate_token_metadata(
    project_id: Optional[int] = typer.Option(None, "--project-id", "-i", help="Project ID (optional; used for defaults and default output path)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Token name (required if no project)"),
    symbol: Optional[str] = typer.Option(None, "--symbol", "-s", help="Token symbol e.g. DRAFT (required if no project)"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Token description"),
    image: Optional[str] = typer.Option(None, "--image", help="URL to token icon/image"),
    external_url: Optional[str] = typer.Option(None, "--external-url", help="Project or website URL"),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output JSON file path (default: data/metadata_<project_id>.json or data/metadata.json)",
    ),
    upload_to_ipfs_flag: bool = typer.Option(
        False,
        "--upload-to-ipfs",
        help="Upload the metadata JSON to IPFS and print the token_uri (set PINATA_JWT for Pinata, or run ipfs daemon)",
    ),
) -> None:
    """Generate token metadata JSON (name, symbol, icon, description, etc.). Use --upload-to-ipfs to auto-upload and get token_uri."""
    project = get_project(project_id) if project_id is not None else None
    if project:
        token_name = name or project.get("token_name") or project["name"]
        token_symbol = symbol or project.get("token_symbol") or "".join(c[0].upper() for c in project["name"].split() if c)[:10] or "TKN"
        token_description = description or project.get("token_description") or project.get("description") or ""
        token_image = image or project.get("token_image") or ""
        token_external_url = external_url or project.get("token_external_url") or project.get("github") or ""
        out_path = output or f"data/metadata_{project_id}.json"
    else:
        if not name or not symbol:
            console.print("[red]No project found. Provide --name and --symbol to generate metadata without a project.[/red]")
            raise typer.Exit(1)
        token_name = name
        token_symbol = symbol
        token_description = description or ""
        token_image = image or ""
        token_external_url = external_url or ""
        out_path = output or (f"data/metadata_{project_id}.json" if project_id is not None else "data/metadata.json")
    try:
        path = write_metadata_json(
            out_path,
            name=token_name,
            symbol=token_symbol,
            description=token_description,
            image=token_image,
            external_url=token_external_url,
        )
    except Exception as e:
        console.print(f"[red]Failed to write metadata: {e}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Metadata JSON written to [cyan]{path}[/cyan][/green]")
    token_uri: Optional[str] = None
    if upload_to_ipfs_flag:
        console.print("Uploading to IPFS...")
        try:
            token_uri = upload_to_ipfs(path)
            console.print(f"[green]Uploaded. Token URI (use as --token-uri):[/green]")
            console.print(f"  [cyan]{token_uri}[/cyan]")
        except Exception as e:
            console.print(f"[red]IPFS upload failed: {e}[/red]")
            raise typer.Exit(1)
    else:
        console.print("Contents: name, symbol, description, image, external_url (Metaplex standard).")
    console.print("Next: create the mint on Devnet:")
    uri_placeholder = token_uri if token_uri else "<YOUR_UPLOADED_JSON_URL>"
    if project_id is not None:
        console.print(f"  startup-cli create-mint --project-id {project_id} --keypair <path> --token-name \"{token_name}\" --token-symbol {token_symbol} --token-uri \"{uri_placeholder}\"")
    else:
        console.print(f"  startup-cli create-mint --project-id <id> --keypair <path> --token-name \"{token_name}\" --token-symbol {token_symbol} --token-uri \"{uri_placeholder}\"")


@app.command("list-projects")
def list_projects_cmd() -> None:
    """List all projects."""
    projects = list_projects()
    if not projects:
        console.print("No projects yet. Create one with create-project.")
        return
    table = Table(title="Projects")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Curve", style="yellow")
    table.add_column("Supply", justify="right")
    table.add_column("Sold", justify="right")
    table.add_column("Treasury (SOL)", justify="right")
    table.add_column("Mint", style="dim")
    for p in projects:
        mint = p.get("mint_address")
        mint_short = (mint[:8] + "..." + mint[-8:]) if mint and len(mint) > 20 else (mint or "-")
        table.add_row(
            str(p["id"]),
            p["name"],
            p["curve_type"],
            str(p["supply"]),
            str(p["tokens_sold"]),
            f"{p['treasury_balance']:.6f}",
            mint_short,
        )
    console.print(table)
    console.print("[dim]Use 'startup-cli addresses --project-id <id>' to see full addresses. Run create-mint to create project token mint.[/dim]")


@app.command()
def addresses(
    project_id: int = typer.Option(..., "--project-id", "-i", help="Project ID"),
) -> None:
    """Show Solana addresses for a project (for blockchain lookup on Devnet)."""
    project = get_project(project_id)
    if not project:
        console.print(f"[red]Project with ID {project_id} not found.[/red]")
        raise typer.Exit(1)
    project_addr, treasury_addr = get_project_addresses(project_id)
    devnet = "https://explorer.solana.com"
    console.print(f"[bold]{project['name']}[/bold] (ID {project_id})")
    console.print()
    console.print("Project account (on-chain project state):")
    console.print(f"  [cyan]{project_addr}[/cyan]")
    console.print(f"  [dim]{devnet}/address/{project_addr}?cluster=devnet[/dim]")
    console.print()
    console.print("Treasury account (SOL / funds):")
    console.print(f"  [cyan]{treasury_addr}[/cyan]")
    console.print(f"  [dim]{devnet}/address/{treasury_addr}?cluster=devnet[/dim]")
    mint = project.get("mint_address")
    if mint:
        console.print()
        console.print("Project token mint (SPL token – the traded token):")
        console.print(f"  [cyan]{mint}[/cyan]")
        console.print(f"  [dim]{devnet}/address/{mint}?cluster=devnet[/dim]")
    else:
        console.print()
        console.print("[dim]No mint yet. Run: startup-cli create-mint --project-id " + str(project_id) + " --keypair <path>[/dim]")
    vault = project.get("vault_owner")
    if vault:
        console.print()
        console.print("Vault owner (wallet that ran create-mint; sell sends tokens here):")
        console.print(f"  [cyan]{vault}[/cyan]")
        console.print("[dim]Use this as --vault-authority when selling if needed.[/dim]")
    else:
        console.print()
        console.print("[dim]Vault owner not stored. Get it with: startup-cli vault-owner --keypair <path-to-create-mint-keypair>[/dim]")


@app.command("vault-owner")
def vault_owner_cmd(
    keypair: str = typer.Option(..., "--keypair", "-k", help="Path to keypair JSON (e.g. the one used for create-mint)"),
) -> None:
    """Print the vault owner address (public key) for a keypair. Use the same keypair as create-mint; pass this as --vault-authority when selling if the project has no vault_owner stored."""
    try:
        kp = load_keypair(keypair)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    pubkey = str(kp.pubkey())
    console.print("Vault owner address (use as --vault-authority for sell-tokens):")
    console.print(f"  [cyan]{pubkey}[/cyan]")
    console.print("[dim]This is the wallet that holds the pre-minted supply; sell sends tokens back to this wallet's token account.[/dim]")


@app.command()
def price(
    project_id: int = typer.Option(..., "--project-id", "-i", help="Project ID"),
    amount: Optional[int] = typer.Option(None, "--amount", "-a", help="Estimate cost for this many tokens"),
) -> None:
    """Show current token price (and optional cost for --amount tokens)."""
    project = get_project(project_id)
    if not project:
        console.print(f"[red]Project with ID {project_id} not found.[/red]")
        raise typer.Exit(1)

    current = get_current_price(
        curve_type=project["curve_type"],
        base_price=project["initial_price"],
        tokens_sold=project["tokens_sold"],
        price_increment=project.get("price_increment"),
        k=project.get("k"),
    )
    console.print(f"Project: [bold]{project['name']}[/bold] (ID {project_id})")
    console.print(f"Current token price: [green]{current:.8f} SOL[/green]")
    console.print(f"Tokens sold: {project['tokens_sold']} / {project['supply']}")

    if amount is not None:
        if project["tokens_sold"] + amount > project["supply"]:
            console.print(f"[red]Cannot buy {amount} tokens; only {project['supply'] - project['tokens_sold']} remaining.[/red]")
            raise typer.Exit(1)
        cost, price_after = calculate_purchase_cost(
            curve_type=project["curve_type"],
            base_price=project["initial_price"],
            tokens_sold=project["tokens_sold"],
            amount=amount,
            price_increment=project.get("price_increment"),
            k=project.get("k"),
        )
        console.print(f"Cost for {amount} tokens (MVP approx): [green]{cost:.8f} SOL[/green]")
        console.print(f"Price after purchase: {price_after:.8f} SOL")


@app.command()
def gui() -> None:
    """Open the Tkinter GUI: view token price and run Create project, Create mint, Buy, Sell, etc."""
    from .gui import main as gui_main
    gui_main()


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Bind host (0.0.0.0 = all network adapters, 127.0.0.1 = localhost only)"),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", help="Reload on code change (development)"),
) -> None:
    """Run the FastAPI server for your frontend. Default 0.0.0.0 so the API is reachable from other devices and via public IP (e.g. on AWS). API docs at http://<host>:<port>/docs."""
    import uvicorn
    if host == "0.0.0.0":
        console.print("[dim]Listening on all interfaces (0.0.0.0). On AWS/cloud, use the instance public IPv4 and open the port in the security group.[/dim]")
    console.print(f"[green]API:[/green] http://{host}:{port}  [dim]Docs:[/dim] http://{host}:{port}/docs")
    uvicorn.run("src.api:app", host=host, port=port, reload=reload)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
