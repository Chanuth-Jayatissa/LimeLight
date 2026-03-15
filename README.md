# Startup CLI

CLI for launching **tokenized startup projects** on Solana Devnet. Investors buy project tokens with SOL; token price is determined by a **bonding curve** (linear or exponential).

## Features

- **Fixed supply** — every project has a **limited supply of 100,000 tokens** (configurable via `--supply`). No minting on buy; tokens are pre-minted and transferred from a vault.
- **Bonding curve** — price is set by the curve over the fixed supply (linear or exponential). As tokens are sold, price increases.
- **Create projects** with name, description, GitHub, and bonding curve params (supply defaults to 100k)
- **Mint SPL tokens** per project — one mint per project with **100k tokens pre-minted** to the vault
- **Linear curve:** `price = base_price + (tokens_sold * price_increment)`
- **Exponential curve:** `price = base_price * e^(k * tokens_sold)`
- **Buy tokens** — investors pay SOL (bonding-curve price) and receive tokens via **transfer from vault** (no new minting)
- **Sell tokens** — token holders send tokens back to the project vault; price from bonding curve; project owner pays SOL (or use a DEX)
- **Tkinter GUI** — view **current token price** and run all actions (create project, create mint, buy, sell) from one window; price updates when you buy/sell
- **Phantom wallet** — connect Phantom in the browser to buy/sell without exporting your keypair; the app opens a local page where you connect and sign
- **Customize tokens** — name, symbol, icon, description, external URL via metadata (Metaplex standard)
- Deterministic, safe bonding curve math in `src/bonding_curve.py`

## Install

```bash
pip install -e .
# or
pip install -r requirements.txt
```

Then run:

```bash
startup-cli --help
# or
python -m src.cli --help
```

### GUI (view price and run all features)

To see the **current trading price** of minted tokens and run Create project, Create mint, Buy, and Sell from one window:

```bash
startup-cli gui
# or
python -m src.gui
```

- Select a project in the list to see its **current token price** (SOL per token) and details.
- **Buy** increases the price; **Sell** decreases it (bonding curve).
- Buttons: Create project, Create mint, Buy tokens, Sell tokens, Addresses, Delete project.
- **Phantom:** Click **Connect Phantom** to open a browser tab; connect your Phantom wallet there, then click **Refresh** in the app. Your address is used as the buyer when you click Buy, and you can **Sell** with "Sign with Phantom" (no keypair file; you sign in the browser). **Use Devnet:** In Phantom go to Settings → Developer Settings → turn on **Testnet Mode** → select **Solana Devnet**. Transactions from this app go to Devnet only.

### FastAPI server (for your frontend webapp)

Run a REST API so your frontend can create projects, get prices, buy/sell, etc.:

```bash
startup-cli serve
# or with port
startup-cli serve --port 8000
# development with auto-reload
startup-cli serve --reload
```

- **API docs (Swagger):** http://localhost:8000/docs  
- **ReDoc:** http://localhost:8000/redoc  
- **CORS** is enabled for all origins so your frontend can call the API.

**Automated flow (no user keypairs):** Set `PLATFORM_KEYPAIR_BASE64` or `PLATFORM_KEYPAIR_PATH` in your env (see `.env.example`). Then:
- **Create project:** `POST /projects` with project data (and optionally `upload_to_ipfs: true`). With `create_mint: true` (default), the server creates the project and mints tokens in one call; the vault is the platform wallet.
- **Buy:** `POST /projects/{id}/buy` with `amount` and `buyer_pubkey` only (e.g. user's Phantom address). No keypair needed from the user.
- **Sell:** User signs with Phantom. Call `POST /projects/{id}/sell/prepare` with `amount` and `seller_pubkey`, then have the user sign in Phantom, then `POST /projects/{id}/sell/confirm` with the signed transaction and `amount`. The vault address is stored with the project; use `GET /projects/{id}/vault` to get it by project ID.

Endpoints include: `GET/POST/DELETE /projects`, `GET /projects/{id}/price`, `GET /projects/{id}/vault`, `POST /projects/{id}/mint`, `POST /projects/{id}/buy`, `POST /projects/{id}/sell/prepare`, `POST /projects/{id}/sell/confirm`, `POST /token-metadata`. See **API_DOC.md** for the full REST API and request bodies.

## Usage

### Create a project (linear curve)

Supply defaults to **100,000** (fixed limited supply for the bonding curve). Override with `--supply` if needed.

```bash
startup-cli create-project \
  --name "Draftt AI" \
  --description "AI video editing platform" \
  --github "https://github.com/example/draftt" \
  --initial-price 0.01 \
  --curve-type linear \
  --price-increment 0.00001
```

### Create a project (exponential curve)

```bash
startup-cli create-project \
  --name "My Startup" \
  --description "Next-gen tooling" \
  --github "https://github.com/example/repo" \
  --initial-price 0.01 \
  --curve-type exponential \
  --k 0.0005
```

### Customize minted tokens (name, icon, description)

You can attach **name**, **symbol**, **icon**, **description**, and more so wallets and explorers show your token properly.

**Option 1 – Set when creating the project**

```bash
startup-cli create-project \
  --name "Draftt AI" \
  --description "AI video editing" \
  --github "https://github.com/example/draftt" \
  --supply 100000 --initial-price 0.01 --curve-type linear --price-increment 0.00001 \
  --token-name "Draftt AI Token" \
  --token-symbol "DRAFT" \
  --token-description "Community token for Draftt AI" \
  --token-image "https://example.com/icon.png" \
  --token-external-url "https://draftt.ai"
```

**Option 2 – Generate metadata JSON, then create mint with URI**

1. Generate the standard metadata JSON (name, symbol, description, image, external_url):

```bash
startup-cli generate-token-metadata --project-id 1 \
  --name "Draftt AI Token" \
  --symbol "DRAFT" \
  --description "Community token for Draftt AI" \
  --image "https://example.com/icon.png" \
  --external-url "https://draftt.ai" \
  --output data/metadata_1.json
```

2. **Auto-upload to IPFS:** use `--upload-to-ipfs` (requires `PINATA_JWT` from [Pinata](https://app.pinata.cloud)):

```bash
export PINATA_JWT="your_jwt_here"
startup-cli generate-token-metadata --project-id 1 \
  --name "Draftt AI Token" --symbol "DRAFT" \
  --description "Community token" --image "https://example.com/icon.png" \
  --external-url "https://draftt.ai" --output data/metadata_1.json --upload-to-ipfs
```

The command prints the **token_uri** (IPFS gateway URL). Copy it for the next step.

   Or upload `data/metadata_1.json` manually to IPFS/Arweave and copy the URL.

3. Create the mint on **Devnet** with that URL as `--token-uri` (and name/symbol for on-chain metadata):

```bash
startup-cli create-mint --project-id 1 --keypair ~/.config/solana/id.json \
  --token-name "Draftt AI Token" \
  --token-symbol "DRAFT" \
  --token-uri "https://arweave.net/your-uploaded-json-id"
```

When **name**, **symbol**, and **token-uri** are all set, the CLI creates **Metaplex metadata** on-chain so Phantom and other wallets show the token name and fetch the icon from the JSON at `token_uri`.

### Create project token mint (SPL)

Each project has its own **minted token** on Devnet. Create the mint once per project (payer = mint authority):

```bash
startup-cli create-mint --project-id 1 --keypair ~/.config/solana/id.json
```

With optional metadata (see above):

```bash
startup-cli create-mint --project-id 1 --keypair ~/.config/solana/id.json \
  --token-name "My Token" --token-symbol "TKN" --token-uri "https://..."
```

The mint is created on **Solana Devnet**. The CLI prints a **View mint on Devnet** link (Solana Explorer); open it to see your token on the blockchain. The mint address is stored and used when investors buy tokens.

### Buy tokens (receive minted project tokens)

Investors pay SOL (price from the bonding curve) and receive the project’s **minted SPL tokens** in their wallet.

If the project has a mint (you ran `create-mint`), provide the buyer’s wallet and the mint-authority keypair so the CLI can mint tokens on-chain:

```bash
startup-cli buy-tokens --project-id 1 --amount 50 --buyer <WALLET_PUBKEY> --keypair ~/.config/solana/id.json
```

The CLI displays:

- Current token price (SOL)
- Total cost (MVP approximation: `current_price * amount`)
- Tokens remaining (before/after)
- Treasury balance (before/after)
- Project token mint address (if set)

Without a project mint, `buy-tokens` only updates local state; use `create-mint` then buy with `--buyer` and `--keypair` to mint real tokens to the buyer.

### Sell tokens (from Phantom or any wallet)

If you hold project tokens in **Phantom** (or any wallet) and want to sell them back:

1. **Export your wallet keypair** (the one that holds the tokens). In Phantom: Settings → Security & Privacy → Export Private Key. Save the keypair JSON to a file (e.g. `phantom_keypair.json`). Keep this file secret and never commit it.
2. Run the CLI with that keypair so it can sign the transfer of tokens from your wallet to the project vault:

```bash
startup-cli sell-tokens --project-id 1 --amount 50 --keypair phantom_keypair.json
```

The CLI will:

- Show current price and how much SOL you receive (from the bonding curve)
- Transfer your tokens from your wallet to the project vault on-chain
- Update local state (tokens_sold and treasury)

**Note:** The CLI does not send SOL to you automatically. The **project owner** is expected to send you the SOL (or you use a DEX). For projects created with `create-mint`, the project stores the vault owner; if you get "no vault_owner", pass `--vault-authority <pubkey>` (see below).

**How to get the vault owner address**

The vault owner is the **wallet that ran `create-mint`** (the keypair that paid for the mint and holds the pre-minted supply). You can get its address in two ways:

1. **From the keypair file** (same keypair used for `create-mint`):
   ```bash
   startup-cli vault-owner --keypair ~/.config/solana/id.json
   ```
   Copy the printed pubkey and use it as `--vault-authority` when selling.

2. **From project state** (if the project was created with a recent CLI that stores it):
   ```bash
   startup-cli addresses --project-id 1
   ```
   If the project has a vault owner stored, it is printed at the bottom. Otherwise use (1).

In the **GUI**, the Sell dialog has a **Vault owner (pubkey)** field: it is pre-filled when the project has it; otherwise enter the address from (1) or (2).

### View addresses (for blockchain lookup)

Each project has deterministic **Solana addresses** (PDAs) you can look up on Devnet:

```bash
startup-cli addresses --project-id 1
```

This prints the **project account** and **treasury account** addresses and Explorer links. Addresses are also shown when you create a project and in `list-projects` (truncated) and `buy-tokens`.

To use your deployed program’s addresses, set the program ID:

```bash
# Windows (PowerShell)
$env:STARTUP_CLI_PROGRAM_ID = "YourDeployedProgramId..."

# Linux/macOS
export STARTUP_CLI_PROGRAM_ID=YourDeployedProgramId...
```

Then the CLI will derive addresses that match your on-chain program.

### Other commands

- `startup-cli list-projects` — list all projects (includes mint address if set)
- `startup-cli delete-project --project-id <id> [--force]` — delete a project from local state (on-chain mint/accounts are not removed)
- `startup-cli create-mint --project-id <id> --keypair <path> [--token-name --token-symbol --token-uri]` — create SPL mint (optionally with metadata)
- `startup-cli sell-tokens --project-id <id> --amount <n> --keypair <path> [--vault-authority <pubkey>]` — sell tokens from your wallet back to the project vault; use `--vault-authority` if the project has no vault owner stored
- `startup-cli vault-owner --keypair <path>` — print the vault owner address (pubkey) for a keypair; use the same keypair as create-mint
- `startup-cli generate-token-metadata --project-id <id> [--name --symbol --description --image --external-url] [-o path]` — write metadata JSON for upload to IPFS/Arweave
- `startup-cli price --project-id 1 [--amount 100]` — show current price and optional cost estimate
- `startup-cli addresses --project-id 1` — show full Solana addresses (project, treasury, mint) and Explorer links
- `startup-cli gui` — open Tkinter GUI to view token price and run all features
- `startup-cli serve [--host 0.0.0.0] [--port 8000] [--reload]` — run FastAPI server for frontend (docs at /docs)

## Bonding curve module

`src/bonding_curve.py` provides:

- `calculate_price_linear(base_price, tokens_sold, price_increment)` → current price
- `calculate_price_exponential(base_price, tokens_sold, k)` → current price
- `calculate_purchase_cost(curve_type, base_price, tokens_sold, amount, ...)` → `(cost, price_after)`

All calculations are deterministic and use only the given numeric inputs.

## Data

Project state is stored in `data/projects.json` (created automatically).
