# API & User Inputs Reference

This document lists every **user-facing input**: CLI options and GUI form fields. All inputs that the user provides when using the Startup CLI or the GUI are listed here.

---

## Bonding curve formulas (price increment / k)

You can set **price_increment** (linear) or **k** (exponential) explicitly, or **derive** them from a target end price (price when all supply is sold):

| Curve | Price formula | Derived parameter |
|-------|----------------|--------------------|
| **Linear** | `price = initial_price + (tokens_sold × price_increment)` | `price_increment = (end_price − initial_price) / supply` |
| **Exponential** | `price = initial_price × e^(k × tokens_sold)` | `k = ln(end_price / initial_price) / supply` |

Alternatively use a **price multiplier** (e.g. 10 ⇒ end price = 10 × initial price):

- **Linear:** `price_increment = (initial_price × (multiplier − 1)) / supply`
- **Exponential:** `k = ln(multiplier) / supply`

If you omit both curve params and any target, the API/CLI default is **price_multiplier = 10** (price at full supply is 10× the initial price).

---

## 1. Environment variables (user-configured)

| Variable | Purpose | Example |
|----------|---------|---------|
| `SOLANA_RPC_URL` | Solana RPC endpoint (optional). If unset, Devnet is used. | `https://api.devnet.solana.com` |
| `PINATA_JWT` | Pinata API JWT for IPFS uploads (optional). Required for `--upload-to-ipfs`. | Your JWT from [Pinata](https://app.pinata.cloud) |
| `STARTUP_CLI_PROGRAM_ID` | Program ID for PDA derivation (optional). | Solana program pubkey |
| `PLATFORM_KEYPAIR_BASE64` | (API) Base64-encoded 64-byte keypair. Used to create mints and sign buys so users don't send keypairs. | From keypair file: base64 encode the 64 bytes |
| `PLATFORM_KEYPAIR_PATH` | (API) Path to keypair JSON file. Alternative to `PLATFORM_KEYPAIR_BASE64`. | `~/.config/solana/id.json` |

---

## 2. CLI commands and user inputs

### 2.1 `create-project`

Creates a new tokenized startup project.

| Input (option) | Short | Type | Required | Default | Description |
|----------------|-------|------|----------|---------|-------------|
| `--name` | `-n` | string | Yes | — | Project name |
| `--description` | `-d` | string | Yes | — | Short description |
| `--github` | `-g` | string | Yes | — | GitHub URL |
| `--supply` | `-s` | int | No | 100000 | Total token supply |
| `--initial-price` | `-p` | float | Yes | — | Initial token price (SOL) |
| `--curve-type` | `-c` | string | No | linear | Bonding curve: `linear` or `exponential` |
| `--price-increment` | — | float | If linear (or use target) | — | Price growth per token (linear curve). Omit to derive from --target-end-price or --price-multiplier. |
| `--k` | — | float | If exponential (or use target) | — | Growth constant (exponential). Omit to derive from --target-end-price or --price-multiplier. |
| `--target-end-price` | — | float | No | — | Target price when supply is fully sold; used to derive price_increment or k |
| `--price-multiplier` | — | float | No | 10 | End price = initial_price × this; used to derive curve params (default 10× at full supply) |
| `--token-name` | — | string | No | — | Token display name for mint metadata |
| `--token-symbol` | — | string | No | — | Token symbol (e.g. DRAFT) |
| `--token-uri` | — | string | No | — | URL to token metadata JSON |
| `--token-description` | — | string | No | — | Token description |
| `--token-image` | — | string | No | — | URL to token icon image |
| `--token-external-url` | — | string | No | — | Project or website URL |
| `--upload-to-ipfs` | — | flag | No | false | Upload token metadata to IPFS (needs `PINATA_JWT`) |

---

### 2.2 `delete-project`

Deletes a project from local state.

| Input (option) | Short | Type | Required | Default | Description |
|----------------|-------|------|----------|---------|-------------|
| `--project-id` | `-i` | int | Yes | — | Project ID to delete |
| `--force` | `-f` | flag | No | false | Skip confirmation |

---

### 2.3 `create-mint`

Creates an SPL token mint on Devnet and pre-mints supply to the vault.

| Input (option) | Short | Type | Required | Default | Description |
|----------------|-------|------|----------|---------|-------------|
| `--project-id` | `-i` | int | Yes | — | Project ID |
| `--keypair` | `-k` | string | Yes | — | Path to payer/mint-authority keypair JSON |
| `--token-name` | — | string | No | From project | Token name (overrides project) |
| `--token-symbol` | — | string | No | From project | Token symbol |
| `--token-uri` | — | string | No | From project | URL to metadata JSON |

---

### 2.4 `buy-tokens`

Buy project tokens (pay SOL, receive SPL tokens).

| Input (option) | Short | Type | Required | Default | Description |
|----------------|-------|------|----------|---------|-------------|
| `--project-id` | `-i` | int | Yes | — | Project ID |
| `--amount` | `-a` | int | Yes | — | Number of tokens to buy |
| `--buyer` | `-b` | string | If mint exists | — | Buyer wallet address (pubkey) |
| `--keypair` | `-k` | string | If mint exists | — | Path to mint-authority keypair |

---

### 2.5 `sell-tokens`

Sell project tokens back to the vault.

| Input (option) | Short | Type | Required | Default | Description |
|----------------|-------|------|----------|---------|-------------|
| `--project-id` | `-i` | int | Yes | — | Project ID |
| `--amount` | `-a` | int | Yes | — | Number of tokens to sell |
| `--keypair` | `-k` | string | Yes | — | Path to wallet keypair (holds the tokens) |
| `--vault-authority` | — | string | No | From project | Vault owner pubkey (where tokens go) |

---

### 2.6 `generate-token-metadata`

Generate token metadata JSON (and optionally upload to IPFS).

| Input (option) | Short | Type | Required | Default | Description |
|----------------|-------|------|----------|---------|-------------|
| `--project-id` | `-i` | int | No | — | Project ID (for defaults and output path) |
| `--name` | `-n` | string | If no project | — | Token name |
| `--symbol` | `-s` | string | If no project | — | Token symbol |
| `--description` | `-d` | string | No | — | Token description |
| `--image` | — | string | No | — | URL to token icon/image |
| `--external-url` | — | string | No | — | Project or website URL |
| `--output` | `-o` | string | No | data/metadata_&lt;id&gt;.json | Output file path |
| `--upload-to-ipfs` | — | flag | No | false | Upload JSON to IPFS (needs `PINATA_JWT`) |

---

### 2.7 `list-projects`

Lists all projects. No user inputs.

---

### 2.8 `addresses`

Shows Solana addresses for a project.

| Input (option) | Short | Type | Required | Default | Description |
|----------------|-------|------|----------|---------|-------------|
| `--project-id` | `-i` | int | Yes | — | Project ID |

---

### 2.9 `vault-owner`

Prints the vault owner address (pubkey) for a keypair.

| Input (option) | Short | Type | Required | Default | Description |
|----------------|-------|------|----------|---------|-------------|
| `--keypair` | `-k` | string | Yes | — | Path to keypair JSON (e.g. create-mint keypair) |

---

### 2.10 `price`

Shows current token price (and optional cost for an amount).

| Input (option) | Short | Type | Required | Default | Description |
|----------------|-------|------|----------|---------|-------------|
| `--project-id` | `-i` | int | Yes | — | Project ID |
| `--amount` | `-a` | int | No | — | Estimate cost for this many tokens |

---

### 2.11 `gui`

Opens the Tkinter GUI. No user inputs.

---

## 3. GUI inputs (forms and actions)

### 3.1 Main window

| Input | Type | Description |
|-------|------|-------------|
| Project list selection | selection | Click a project in the list to select it (used for all project-scoped actions). |
| **Connect Phantom** | button | Opens browser tab for Phantom connect. |
| **Refresh** | button | Refreshes Phantom connection status. |
| **Create project** | button | Opens Create project dialog. |
| **Create mint** | button | Opens Create mint dialog (requires selected project). |
| **Buy tokens** | button | Opens Buy tokens dialog (requires selected project). |
| **Sell tokens** | button | Opens Sell tokens dialog (requires selected project). |
| **Addresses** | button | Shows addresses for selected project. |
| **Delete project** | button | Deletes selected project (with confirmation). |

---

### 3.2 Create project (dialog)

| Field / control | Type | Required | Default | Description |
|-----------------|------|----------|---------|-------------|
| Name | text | Yes | — | Project name |
| Description | text | No | (empty) | Short description |
| GitHub URL | text | No | https://github.com | GitHub URL |
| Supply | text (int) | Yes | 100000 | Total token supply |
| Initial price (SOL) | text (float) | Yes | 0.01 | Initial token price in SOL |
| Curve type | dropdown | Yes | linear | `linear` or `exponential` |
| Price increment (linear) | text (float) | If linear | 0.00001 | Price growth per token |
| k (exponential) | text (float) | If exponential | 0.0005 | Growth constant |
| Upload token metadata to IPFS | checkbox | No | false | Upload metadata (needs PINATA_JWT) |
| **Create** | button | — | — | Submits the form |
| **Cancel** | button | — | — | Closes dialog |

---

### 3.3 Create mint (dialog)

| Field / control | Type | Required | Default | Description |
|-----------------|------|----------|---------|-------------|
| Keypair path | text | Yes | — | Path to payer/mint-authority keypair JSON |
| Browse | button | — | — | File picker for keypair |
| Token name | text | No | From project | Token name |
| Token symbol | text | No | From project | Token symbol |
| Token URI | text | No | From project | URL to metadata JSON |
| **Create mint** | button | — | — | Creates mint on Devnet |
| **Cancel** | button | — | — | Closes dialog |

---

### 3.4 Buy tokens (dialog)

| Field / control | Type | Required | Default | Description |
|-----------------|------|----------|---------|-------------|
| Amount (tokens) | text (int) | Yes | 10 | Number of tokens to buy |
| Buyer wallet (pubkey) | text | Yes (if mint) | Phantom if connected | Buyer wallet address |
| Mint authority keypair | text | Yes (if mint) | — | Path to mint-authority keypair |
| Browse | button | — | — | File picker for keypair |
| **Buy** | button | — | — | Executes buy (after confirm) |
| **Cancel** | button | — | — | Closes dialog |

---

### 3.5 Sell tokens (dialog)

| Field / control | Type | Required | Default | Description |
|-----------------|------|----------|---------|-------------|
| Amount (tokens) | text (int) | Yes | 10 | Number of tokens to sell |
| Sign with Phantom | checkbox | No | true if Phantom connected | Sign in browser (no keypair file) |
| Or keypair (wallet holding tokens) | text | If not Phantom | — | Path to seller keypair JSON |
| Browse | button | — | — | File picker for keypair |
| Vault owner (pubkey) | text | Yes | From project if set | Vault owner address (get via `vault-owner` if missing) |
| **Sell** | button | — | — | Executes sell (after confirm) |
| **Cancel** | button | — | — | Closes dialog |

---

### 3.6 Addresses (dialog)

Shows project account, treasury, mint, and vault owner. No user inputs except closing the dialog.

---

### 3.7 Delete project (dialog)

| Input | Type | Description |
|-------|------|-------------|
| Confirmation | yes/no | Confirm deletion of the selected project |
| **Cancel** | — | Aborts deletion |

---

## 4. Phantom browser page (Connect / Sign)

User actions on the page opened by **Connect Phantom**:

| Action | Description |
|--------|-------------|
| Set Phantom to Devnet | User must set Phantom: Settings → Developer Settings → Testnet Mode → Solana Devnet. |
| **Connect Phantom** | Button to connect wallet; Phantom prompts for approval. |
| **Disconnect** | Shown after connect; disconnects the wallet. |
| **Refresh** (in GUI) | After connecting in the browser, user clicks Refresh in the app to show connected address. |
| Sign transaction | When user clicks Sell with “Sign with Phantom”, the browser tab shows a transaction to sign; user approves in Phantom. |

---

## 5. Summary table (all user inputs at a glance)

| Source | Command / Screen | Main user inputs |
|--------|------------------|------------------|
| Env | — | `SOLANA_RPC_URL`, `PINATA_JWT`, `STARTUP_CLI_PROGRAM_ID`, `PLATFORM_KEYPAIR_BASE64` or `PLATFORM_KEYPAIR_PATH` (for API) |
| CLI | create-project | name, description, github, supply, initial-price, curve-type, price-increment / k, token metadata opts, upload-to-ipfs |
| CLI | delete-project | project-id, force |
| CLI | create-mint | project-id, keypair, token-name, token-symbol, token-uri |
| CLI | buy-tokens | project-id, amount, buyer, keypair |
| CLI | sell-tokens | project-id, amount, keypair, vault-authority |
| CLI | generate-token-metadata | project-id, name, symbol, description, image, external-url, output, upload-to-ipfs |
| CLI | addresses | project-id |
| CLI | vault-owner | keypair |
| CLI | price | project-id, amount |
| CLI | gui | (none) |
| GUI | Create project | name, description, github, supply, initial price, curve type, price increment / k, upload IPFS |
| GUI | Create mint | keypair path, token name, symbol, URI |
| GUI | Buy tokens | amount, buyer pubkey, mint authority keypair |
| GUI | Sell tokens | amount, Sign with Phantom checkbox, keypair path, vault owner pubkey |
| Phantom page | Connect / Sign | Connect Phantom, set Devnet, approve sign |

---

## 6. REST API (FastAPI server)

Run the server with `startup-cli serve` (default: http://localhost:8000). Interactive docs: **http://localhost:8000/docs**. CORS is enabled for all origins.

Base URL: `http://localhost:8000` (or your host/port).

### Simplified flow (no user keypairs)

Set **one** of `PLATFORM_KEYPAIR_BASE64` or `PLATFORM_KEYPAIR_PATH` in env. Then:

- **Create project:** `POST /projects` with `create_mint: true` (default) → project + mint created in one call. Optionally pass `vault_owner` (Solana address) so that wallet holds the pre-minted supply; omit to use platform wallet as vault.
- **Buy:** `POST /projects/{id}/buy` with only `amount` and `buyer_pubkey` (user's wallet address, e.g. from Phantom). No keypair in the request.
- **Sell:** User signs with Phantom. Your frontend: `POST /sell/prepare` with `amount`, `seller_pubkey` → get unsigned tx → user signs in Phantom → `POST /sell/confirm` with `signed_transaction_base64` and `amount`. Vault address is stored per project; use `GET /projects/{id}/vault` if you need to show it.

### 6.1 Projects

| Method | Path | Description | User inputs (body/query) |
|--------|------|-------------|-------------------------|
| GET | `/projects` | List all projects | — |
| GET | `/projects/{project_id}` | Get one project | `project_id` (path) |
| POST | `/projects` | Create project | Body: `CreateProjectRequest` (see below) |
| DELETE | `/projects/{project_id}` | Delete project | `project_id` (path) |

**CreateProjectRequest (JSON body):**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| name | string | Yes | — | Project name |
| description | string | No | "" | Description |
| github | string | No | "https://github.com" | GitHub URL |
| supply | int | No | 100000 | Token supply |
| initial_price | float | No | 0.01 | Initial price (SOL); omitted = auto 0.01 |
| curve_type | string | No | "linear" | "linear" or "exponential"; omitted = auto "linear" |
| price_increment | float | No | derived | Linear: price growth per token; omitted = derived from price_multiplier (default 10×) |
| k | float | No | derived | Exponential: growth constant; omitted = derived |
| token_name, token_symbol, token_uri, token_description, token_image, token_external_url | string | No | — | Token metadata |
| upload_to_ipfs | bool | No | false | Upload metadata to IPFS (needs PINATA_JWT) |
| create_mint | bool | No | true | If true, create SPL mint and set vault (requires PLATFORM_KEYPAIR in env) |
| vault_owner | string | No | — | Solana address that will hold the pre-minted supply. Omit to use platform wallet; when set, tokens are minted to this wallet’s ATA (for buys, send this wallet’s keypair as keypair_base64). |
| target_end_price | float | No | — | Target price when supply is fully sold; used to derive price_increment (linear) or k (exponential) |
| price_multiplier | float | No | 10 if omitted | End price = initial_price × this (e.g. 10 ⇒ 10× at end); used to derive curve params when price_increment/k not set |

### 6.2 Price, addresses, and vault

| Method | Path | Description | User inputs |
|--------|------|-------------|-------------|
| GET | `/projects/{project_id}/price` | Current price; optional cost for amount | `project_id` (path), `amount` (query, optional) |
| GET | `/projects/{project_id}/addresses` | Project, treasury, mint, vault_owner | `project_id` (path) |
| GET | `/projects/{project_id}/vault` | Vault owner and mint for this project (e.g. for sell flow) | `project_id` (path) |

### 6.3 Mint

| Method | Path | Description | User inputs |
|--------|------|-------------|-------------|
| POST | `/projects/{project_id}/mint` | Create SPL mint on Devnet | `project_id` (path), Body: optional `keypair_base64` (if omitted, uses PLATFORM_KEYPAIR), optional `token_name`, `token_symbol`, `token_uri` |

**keypair_base64:** Optional. If omitted, server uses PLATFORM_KEYPAIR from env.

### 6.4 Buy

| Method | Path | Description | User inputs |
|--------|------|-------------|-------------|
| POST | `/projects/{project_id}/buy` | Buy tokens (vault → buyer) | `project_id` (path), Body: `amount`, `buyer_pubkey` (required). Optional `keypair_base64` (if omitted, uses PLATFORM_KEYPAIR). User only needs to send their wallet address as buyer_pubkey. |

### 6.5 Sell (Phantom flow: prepare + confirm)

| Method | Path | Description | User inputs |
|--------|------|-------------|-------------|
| POST | `/projects/{project_id}/sell/prepare` | Get unsigned tx for Phantom | `project_id` (path), Body: `amount`, `seller_pubkey` |
| POST | `/projects/{project_id}/sell/confirm` | Submit signed tx, update state | `project_id` (path), Body: `signed_transaction_base64`, `amount` |
| POST | `/projects/{project_id}/sell` | Sell with keypair (server signs) | `project_id` (path), Body: `amount`, `keypair_base64` |

**Sell flow with Phantom (no keypair from user):**  
1. Optionally GET `/projects/{id}/vault` to show vault address.  
2. POST `/sell/prepare` with `amount` and `seller_pubkey` (user's Phantom wallet). Server uses project's stored vault_owner.  
3. Frontend gets `unsigned_transaction_base64`, has user sign with Phantom.  
4. POST `/sell/confirm` with `signed_transaction_base64` and `amount`.

### 6.6 Token metadata

| Method | Path | Description | User inputs |
|--------|------|-------------|-------------|
| POST | `/token-metadata` | Generate metadata JSON; optional IPFS upload | Body: `project_id?`, `name?`, `symbol?`, `description`, `image`, `external_url`, `output_path?`, `upload_to_ipfs` |

### 6.7 Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check; returns `{"status": "ok"}` |

---

## 7. API endpoints reference (request/response)

Base URL: `http://localhost:8000`. All request bodies are JSON; `Content-Type: application/json`.

### GET /health

**Response:** `200 OK`

```json
{"status": "ok"}
```

---

### GET /projects

**Response:** `200 OK` — array of project objects.

```json
[
  {
    "id": 1,
    "name": "My Token",
    "description": "...",
    "supply": 100000,
    "initial_price": 0.01,
    "curve_type": "linear",
    "price_increment": 9e-7,
    "k": null,
    "tokens_sold": 0,
    "treasury_balance": 0.0,
    "mint_address": "7xKX...",
    "vault_owner": "HjWm...",
    "token_name": "My Token",
    "token_symbol": "MTK"
  }
]
```

---

### GET /projects/{project_id}

**Path:** `project_id` (integer)

**Response:** `200 OK` — single project object. `404` if not found.

---

### POST /projects

**Body:** CreateProjectRequest (see table in §6.1). Minimal example:

```json
{
  "name": "Draftt AI",
  "description": "AI video editing",
  "initial_price": 0.01,
  "supply": 100000,
  "curve_type": "linear",
  "create_mint": true
}
```

Optional: `price_increment`, `k`, `target_end_price`, `price_multiplier`, `upload_to_ipfs`, token metadata fields.

**Response:** `200 OK` — created project (includes `id`, `mint_address`, `vault_owner` if `create_mint` was true).

**Errors:** `400` (validation), `503` (create_mint true but PLATFORM_KEYPAIR not set).

---

### DELETE /projects/{project_id}

**Response:** `200 OK` — `{"status": "deleted", "project_id": "1"}`. `404` if not found.

---

### GET /projects/{project_id}/price

**Query:** `amount` (optional, int) — if set, response includes cost and price_after.

**Response:** `200 OK`

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

**Response:** `200 OK`

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

**Response:** `200 OK`

```json
{
  "vault_owner": "HjWm...",
  "mint": "7xKX..."
}
```

---

### POST /projects/{project_id}/mint

**Body:** Optional `keypair_base64`; optional `token_name`, `token_symbol`, `token_uri`. If keypair omitted, uses PLATFORM_KEYPAIR.

**Response:** `200 OK`

```json
{
  "mint_address": "7xKXtg2...",
  "explorer_url": "https://explorer.solana.com/address/7xKX...?cluster=devnet"
}
```

**Errors:** `503` if no keypair available.

---

### POST /projects/{project_id}/buy

**Body:**

```json
{
  "amount": 50,
  "buyer_pubkey": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
}
```

Optional: `keypair_base64` (if omitted, uses PLATFORM_KEYPAIR).

**Response:** `200 OK`

```json
{
  "signature": "5Vx7...",
  "buyer": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
}
```

**Errors:** `400` (no mint, not enough supply), `503` (no keypair).

---

### POST /projects/{project_id}/sell/prepare

**Body:**

```json
{
  "amount": 20,
  "seller_pubkey": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
}
```

**Response:** `200 OK`

```json
{
  "unsigned_transaction_base64": "AQAAAAAAAAA...",
  "amount": 20,
  "seller_pubkey": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
  "sell_value_sol_approx": 0.2018
}
```

Frontend signs `unsigned_transaction_base64` with Phantom, then POSTs the signed tx to `/sell/confirm`.

---

### POST /projects/{project_id}/sell/confirm

**Body:**

```json
{
  "signed_transaction_base64": "AQAAAAAAAAA...",
  "amount": 20
}
```

**Response:** `200 OK`

```json
{
  "signature": "4Kp2...",
  "amount": 20,
  "sell_value_sol_approx": 0.2018
}
```

---

### POST /projects/{project_id}/sell

**Body:** Sell with server-side keypair (no Phantom).

```json
{
  "amount": 20,
  "keypair_base64": "..."
}
```

**Response:** Same as `/sell/confirm`.

---

### POST /token-metadata

**Body:** Optional `project_id`; optional `name`, `symbol`, `description`, `image`, `external_url`, `output_path`; `upload_to_ipfs` (bool).

**Response:** `200 OK` — metadata JSON path and optional `token_uri` if uploaded.

---

## 8. Example use cases

### Use case 1: Create a project and mint in one call (no keypair in request)

Set `PLATFORM_KEYPAIR_BASE64` or `PLATFORM_KEYPAIR_PATH` in env. Then:

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Draftt AI",
    "description": "AI video editing platform",
    "initial_price": 0.01,
    "supply": 100000,
    "curve_type": "linear",
    "create_mint": true,
    "upload_to_ipfs": false
  }'
```

Response includes `id`, `mint_address`, `vault_owner`. Curve params are derived (default 10× at full supply) if you omit `price_increment` and `k`.

---

### Use case 2: List projects and show current price

```bash
# List all
curl http://localhost:8000/projects

# Get project 1
curl http://localhost:8000/projects/1

# Current price and cost for buying 100 tokens
curl "http://localhost:8000/projects/1/price?amount=100"
```

---

### Use case 3: User buys tokens (frontend has only wallet address)

User connects Phantom; frontend has `buyer_pubkey`. No keypair sent from frontend.

```bash
curl -X POST http://localhost:8000/projects/1/buy \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50,
    "buyer_pubkey": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
  }'
```

---

### Use case 4: User sells tokens with Phantom (prepare → sign in Phantom → confirm)

**Step 1 — Get unsigned transaction:**

```bash
curl -X POST http://localhost:8000/projects/1/sell/prepare \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 20,
    "seller_pubkey": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
  }'
```

Response: `unsigned_transaction_base64`, `amount`, `sell_value_sol_approx`.

**Step 2 — Frontend:** Decode base64 to bytes, build Solana `Transaction`, call Phantom’s `signTransaction(tx)`, serialize signed tx, base64-encode.

**Step 3 — Submit signed transaction:**

```bash
curl -X POST http://localhost:8000/projects/1/sell/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "signed_transaction_base64": "<signed_tx_base64_from_phantom>",
    "amount": 20
  }'
```

---

### Use case 5: Get vault address by project ID (for display or sell flow)

```bash
curl http://localhost:8000/projects/1/vault
```

Response: `vault_owner`, `mint`. Use when you need to show “tokens sell back to this address” or in sell UX.

---

### Use case 6: Create project with custom end price (derive curve params)

Linear curve, end price 0.1 SOL when all 100k tokens sold:

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Custom Curve",
    "description": "Linear 0.01 -> 0.1",
    "initial_price": 0.01,
    "supply": 100000,
    "curve_type": "linear",
    "target_end_price": 0.1,
    "create_mint": true
  }'
```

Or use `price_multiplier`: e.g. `"price_multiplier": 5` for 5× at full supply.

---

### Use case 7: JavaScript/TypeScript fetch examples

```javascript
const BASE = 'http://localhost:8000';

// List projects
const projects = await (await fetch(`${BASE}/projects`)).json();

// Get price for 100 tokens
const price = await (await fetch(`${BASE}/projects/1/price?amount=100`)).json();
console.log(price.cost_sol, price.current_price_sol);

// Create project (with platform keypair in env)
const created = await (await fetch(`${BASE}/projects`, {
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
})).json();

// Buy (user's wallet from Phantom)
const buyResult = await (await fetch(`${BASE}/projects/1/buy`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ amount: 50, buyer_pubkey: userWalletPublicKey }),
})).json();
console.log('Tx:', buyResult.signature);
```

---

### Use case 8: Health check (load balancer / readiness)

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```
