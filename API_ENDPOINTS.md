# API Endpoints Reference

Start the server: `startup-cli serve` (default: **http://localhost:8000**).  
Interactive docs: **http://localhost:8000/docs**

All request bodies are JSON. Use header: `Content-Type: application/json`.

---

## Health

### GET /health

Check that the API is running.

**Example**

```bash
curl http://localhost:8000/health
```

**Response** `200 OK`

```json
{"status": "ok"}
```

---

## Projects

### GET /projects

List all projects.

**Example**

```bash
curl http://localhost:8000/projects
```

**Response** `200 OK` — array of project objects.

**Example output**

```json
[
  {
    "id": 1,
    "name": "Draftt AI",
    "description": "Video Editting",
    "github": "https://github.com/example/draftt",
    "supply": 100000,
    "initial_price": 0.01,
    "curve_type": "linear",
    "price_increment": 1e-05,
    "k": null,
    "tokens_sold": 100,
    "treasury_balance": 1.025,
    "active": false,
    "stake_deposited": false,
    "mint_address": "3qULpH9dR6v1QyELXL6eBi93jdNP4gXCabk7FLZdLnA1",
    "vault_owner": "HjWm4BsLyVNrTz8ZFbY5ycS9Sm6cDyN3W22bWQ3A7DcR",
    "token_name": "Draftt AI Token",
    "token_symbol": "DRAFT",
    "token_uri": "https://gateway.pinata.cloud/ipfs/Qmd6jpbd5vmoJZUeNdpARu5MJg98D2ewEahkT43yHDaxXS",
    "token_description": "Video Editting",
    "token_image": "https://example.com/icon.svg",
    "token_external_url": "https://drafft.tech"
  },
]
```

---

### GET /projects/{project_id}

Get one project by ID.

**Example**

```bash
curl http://localhost:8000/projects/1
```

**Response** `200 OK` — single project object. `404` if not found.

**Example output**

```json
{
  "id": 1,
  "name": "Draftt AI",
  "description": "Video Editting",
  "github": "https://github.com/example/draftt",
  "supply": 100000,
  "initial_price": 0.01,
  "curve_type": "linear",
  "price_increment": 1e-05,
  "k": null,
  "tokens_sold": 100,
  "treasury_balance": 1.025,
  "active": false,
  "stake_deposited": false,
  "mint_address": "3qULpH9dR6v1QyELXL6eBi93jdNP4gXCabk7FLZdLnA1",
  "vault_owner": "HjWm4BsLyVNrTz8ZFbY5ycS9Sm6cDyN3W22bWQ3A7DcR",
  "token_name": "Draftt AI Token",
  "token_symbol": "DRAFT",
  "token_uri": "https://gateway.pinata.cloud/ipfs/...",
  "token_description": "Video Editting",
  "token_image": "https://example.com/icon.svg",
  "token_external_url": "https://drafft.tech"
}
```

---

### POST /projects

Create a new project. With `create_mint: true` (default), also creates the SPL mint and sets the vault (requires `PLATFORM_KEYPAIR` in env).

**Body** — All of `initial_price`, `curve_type`, `price_increment`, and `k` are **optional** and auto-generated if omitted (defaults: `0.01` SOL, `linear`, 10× at full supply).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Project name |
| description | string | No | Description (default `""`) |
| github | string | No | GitHub URL (default `"https://github.com"`) |
| supply | int | No | Token supply (default `100000`) |
| initial_price | float | No | Initial token price in SOL (default `0.01`) |
| curve_type | string | No | `"linear"` or `"exponential"` (default `"linear"`) |
| price_increment | float | No | Linear: price growth per token (auto-derived from price_multiplier if omitted) |
| k | float | No | Exponential: growth constant (auto-derived if omitted) |
| target_end_price | float | No | Target price when supply is fully sold (derives price_increment or k) |
| price_multiplier | float | No | End price = initial_price × this (default 10 if curve params omitted) |
| token_name, token_symbol, token_uri, token_description, token_image, token_external_url | string | No | Token metadata |
| upload_to_ipfs | bool | No | Upload metadata to IPFS (default `false`; needs PINATA_JWT) |
| create_mint | bool | No | Create SPL mint and set vault (default `true`; needs PLATFORM_KEYPAIR) |
| vault_owner | string | No | Solana address (base58) that will hold the pre-minted supply. Omit to use platform wallet as vault. When set, tokens are minted to this wallet’s ATA; for buys you must send this wallet’s keypair as `keypair_base64`. |

**Example**

```bash
# Minimal: name only; initial_price (0.01), curve_type (linear), price_increment/k (10x at full supply) are auto-generated
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Draftt AI", "description": "AI video editing", "create_mint": true}'
```

**Response** `200 OK` — created project (includes `id`, and `mint_address` / `vault_owner` if `create_mint` was true).

**Errors** `400` validation, `503` create_mint true but PLATFORM_KEYPAIR not set.

**Create project with a custom vault owner (tokens minted to that wallet):**

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Token",
    "description": "Tokens held by my wallet",
    "create_mint": true,
    "vault_owner": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
  }'
```

The platform still pays for and creates the mint; the pre-minted supply is sent to the `vault_owner`’s token account. For **buy** when the project has a custom vault, you must send the vault owner’s keypair as `keypair_base64` so the server can sign the transfer from that vault to the buyer.

---

**Create project with mint and upload all metadata to IPFS**

Set `upload_to_ipfs: true` and include all token metadata fields. The server builds a Metaplex-style JSON (name, symbol, description, image, external_url), uploads it to IPFS (requires `PINATA_JWT` in env), sets `token_uri` on the project, then creates the mint with that URI so wallets show name, icon, and description. Omit `token_uri` so the server uploads.

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Token",
    "description": "Project description",
    "github": "https://github.com/example/my-token",
    "supply": 100000,
    "create_mint": true,
    "upload_to_ipfs": true,
    "token_name": "My Token",
    "token_symbol": "MTK",
    "token_description": "Full token description for wallets and explorers",
    "token_image": "https://example.com/icon.png",
    "token_external_url": "https://my-token.com",
    "vault_owner": "YOUR_PHANTOM_OR_WALLET_ADDRESS"
  }'
```

Required env: `PINATA_JWT` (for IPFS), `PLATFORM_KEYPAIR_PATH` or `PLATFORM_KEYPAIR_BASE64` (for create_mint). The uploaded JSON includes: `name`, `symbol`, `description`, `image`, `external_url`.

**Copy-paste ready (single line):**

```bash
curl -X POST http://localhost:8000/projects -H "Content-Type: application/json" -d '{"name":"My Token","description":"Project description","supply":100000,"create_mint":true,"upload_to_ipfs":true,"token_name":"My Token","token_symbol":"MTK","token_description":"Full token description","token_image":"https://example.com/icon.png","token_external_url":"https://my-token.com","vault_owner":"YOUR_PHANTOM_ADDRESS"}'
```

Replace `localhost:8000` with your server (e.g. `18.224.183.185:8000`) and `YOUR_PHANTOM_ADDRESS` with the creator's wallet.

---

### DELETE /projects/{project_id}

Delete a project from local state (on-chain data is not removed).

**Example**

```bash
curl -X DELETE http://localhost:8000/projects/1
```

**Response** `200 OK`

```json
{"status": "deleted", "project_id": "1"}
```

`404` if project not found.

---

## Price & addresses

### GET /projects/{project_id}/price

Get current token price. Optional query `amount` returns cost and price after buying that many tokens.

**Query**

| Param | Type | Description |
|-------|------|-------------|
| amount | int | Optional. If set, response includes cost_sol and price_after_sol |

**Example**

```bash
# Current price only
curl http://localhost:8000/projects/1/price

# Price and cost for buying 100 tokens
curl "http://localhost:8000/projects/1/price?amount=100"
```

**Response** `200 OK`

Without `amount`:

```json
{
  "current_price_sol": 0.01,
  "tokens_sold": 0,
  "supply": 100000
}
```

With `?amount=100`:

```json
{
  "current_price_sol": 0.01,
  "tokens_sold": 0,
  "supply": 100000,
  "amount": 100,
  "cost_sol": 1.0,
  "price_after_sol": 0.01009
}
```

---

### GET /projects/{project_id}/addresses

Get project account, treasury, mint, and vault_owner addresses.

**Example**

```bash
curl http://localhost:8000/projects/1/addresses
```

**Response** `200 OK`

```json
{
  "project_account": "...",
  "treasury": "...",
  "mint": "7xKX...",
  "vault_owner": "HjWm..."
}
```

---

### GET /projects/{project_id}/vault

Get only vault_owner and mint for this project (e.g. for sell flow or display).

**Example**

```bash
curl http://localhost:8000/projects/1/vault
```

**Response** `200 OK`

```json
{
  "vault_owner": "HjWm...",
  "mint": "7xKX..."
}
```

---

## Mint

### POST /projects/{project_id}/mint

Create SPL token mint on Devnet and pre-mint full supply to vault. Uses `keypair_base64` from body if provided, otherwise PLATFORM_KEYPAIR from env. Optionally mint to a custom `vault_owner` so that wallet holds the supply.

**Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| keypair_base64 | string | No | Base64 keypair (if omitted, uses PLATFORM_KEYPAIR) |
| vault_owner | string | No | Solana address that will hold the pre-minted supply. Omit to use platform wallet as vault. |
| token_name | string | No | Override token name |
| token_symbol | string | No | Override token symbol |
| token_uri | string | No | Override token metadata URI |

**Example**

```bash
curl -X POST http://localhost:8000/projects/1/mint \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response** `200 OK`

```json
{
  "mint_address": "7xKXtg2...",
  "explorer_url": "https://explorer.solana.com/address/7xKX...?cluster=devnet"
}
```

**Errors** `503` if no keypair available.

---

## Buy

### POST /projects/{project_id}/buy

Transfer tokens from vault to buyer. Uses PLATFORM_KEYPAIR from env if `keypair_base64` is not sent.

**Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| amount | int | Yes | Number of tokens to buy |
| buyer_pubkey | string | Yes | Buyer wallet address (e.g. from Phantom) |
| keypair_base64 | string | No | Mint authority keypair (if omitted, uses PLATFORM_KEYPAIR) |

**Example**

```bash
curl -X POST http://localhost:8000/projects/1/buy \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50,
    "buyer_pubkey": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
  }'
```

**Response** `200 OK`

```json
{
  "signature": "5Vx7...",
  "buyer": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
}
```

**Errors** `400` no mint / not enough supply, `503` no keypair.

---

## Sell (Phantom flow: prepare → sign → confirm)

### POST /projects/{project_id}/sell/prepare

Get an unsigned sell transaction. Frontend signs it with Phantom, then submits via `/sell/confirm`.

**Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| amount | int | Yes | Number of tokens to sell |
| seller_pubkey | string | Yes | Seller wallet (e.g. Phantom) |

**Example**

```bash
curl -X POST http://localhost:8000/projects/1/sell/prepare \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 20,
    "seller_pubkey": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
  }'
```

**Response** `200 OK`

```json
{
  "unsigned_transaction_base64": "AQAAAAAAAAA...",
  "amount": 20,
  "seller_pubkey": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
  "sell_value_sol_approx": 0.2018
}
```

**How to use:** Decode `unsigned_transaction_base64`, have Phantom sign the transaction, base64-encode the signed transaction, then call `/sell/confirm` with it and `amount`.

---

### POST /projects/{project_id}/sell/confirm

Submit the signed sell transaction (from Phantom) and update local state.

**Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| signed_transaction_base64 | string | Yes | Transaction signed by Phantom (base64) |
| amount | int | Yes | Number of tokens sold (for state update) |

**Example**

```bash
curl -X POST http://localhost:8000/projects/1/sell/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "signed_transaction_base64": "<base64_from_phantom>",
    "amount": 20
  }'
```

**Response** `200 OK`

```json
{
  "signature": "4Kp2...",
  "amount": 20,
  "sell_value_sol_approx": 0.2018
}
```

---

### POST /projects/{project_id}/sell

Sell using a keypair (server signs). Use this when not using Phantom; for Phantom use `/sell/prepare` + `/sell/confirm`.

**Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| amount | int | Yes | Number of tokens to sell |
| keypair_base64 | string | Yes | Seller wallet keypair (base64) |

**Example**

```bash
curl -X POST http://localhost:8000/projects/1/sell \
  -H "Content-Type: application/json" \
  -d '{"amount": 20, "keypair_base64": "..."}'
```

**Response** Same shape as `/sell/confirm`.

---

## Token metadata

### POST /token-metadata

Generate token metadata JSON. Optionally upload to IPFS and get token_uri.

**Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| project_id | int | No | Use project's metadata if set |
| name | string | No | Token name |
| symbol | string | No | Token symbol |
| description | string | No | Description |
| image | string | No | Image URL |
| external_url | string | No | External URL |
| output_path | string | No | Where to write JSON |
| upload_to_ipfs | bool | No | Upload and return token_uri |

**Example**

```bash
curl -X POST http://localhost:8000/token-metadata \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "upload_to_ipfs": true
  }'
```

**Response** `200 OK` — metadata path and optional `token_uri` if uploaded.

---

## Quick examples (JavaScript)

```javascript
const BASE = 'http://localhost:8000';

// List projects
const projects = await fetch(`${BASE}/projects`).then(r => r.json());

// Get price for 100 tokens
const price = await fetch(`${BASE}/projects/1/price?amount=100`).then(r => r.json());

// Create project + mint
const created = await fetch(`${BASE}/projects`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'My Token',
    description: 'Example',
    initial_price: 0.01,
    supply: 100000,
    curve_type: 'linear',
    create_mint: true,
  }),
}).then(r => r.json());

// Buy tokens (user's wallet from Phantom)
const buy = await fetch(`${BASE}/projects/1/buy`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ amount: 50, buyer_pubkey: userWalletPublicKey }),
}).then(r => r.json());
```

---

## How the vault address is obtained

The **vault address** (vault owner) is the Solana wallet that holds the project’s pre-minted token supply. It is set **when the mint is created** (either in `POST /projects` with `create_mint: true` or in `POST /projects/{id}/mint`).

1. **You pass `vault_owner`**  
   If you send a `vault_owner` (Solana address, base58) in the create-project or create-mint request, that value is stored as the project’s vault. The tokens are minted to that wallet’s associated token account (ATA).

2. **You omit `vault_owner`**  
   If you don’t send `vault_owner`, the vault is set to the **public key of the keypair used to create the mint**:
   - **API:** the platform keypair from env (`PLATFORM_KEYPAIR_BASE64` or `PLATFORM_KEYPAIR_PATH`), i.e. `str(kp.pubkey())`.
   - **CLI:** the keypair you pass to `create-mint` (e.g. `--keypair ~/.config/solana/id.json`).

So: **Vault = custom address** when you provided `vault_owner`; **Vault = platform (or create-mint) wallet** when you didn’t.

**Where it’s stored and how to read it**

- The vault is saved in project state (`data/projects.json`) as `vault_owner` when the mint is created.
- Read it via **GET /projects/{id}**, **GET /projects/{id}/addresses**, or **GET /projects/{id}/vault**.

**Project creator owns the supply:** Pass the creator's Phantom (or wallet) address as `vault_owner` when creating the project so the person adding the project receives the full pre-minted supply; the platform only pays for the mint.

**CLI:** If a project has no `vault_owner` stored (e.g. created earlier), get the address of the keypair that ran create-mint:  
`startup-cli vault-owner --keypair ~/.config/solana/id.json`  
Use that as `--vault-authority` when selling.

---

## Environment (for automated create/buy without user keypairs)

Set **one** of these so the server can create mints and sign buys:

- **PLATFORM_KEYPAIR_BASE64** — base64-encoded 64-byte keypair
- **PLATFORM_KEYPAIR_PATH** — path to keypair JSON (e.g. `~/.config/solana/id.json`)

See `.env.example` for details.
